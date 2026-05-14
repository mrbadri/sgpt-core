"""Bridge between callers (e.g. Bale bot) and the LangGraph deep agent."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.schema import StreamEvent

from app.agent.prompts import (
    ONBOARDING_PHOTO_LINE,
    ONBOARDING_PROMPT_TEMPLATE,
    PERSONALITY_NO_PHOTO,
    PERSONALITY_WITH_PHOTO,
)
from app.agent.format_response import AgentResponse
from app.plans import INPUT_COST_PER_1M, OUTPUT_COST_PER_1M
from app.settings import settings

# Return type alias: (answer, cost_usd)
AgentResult = tuple[Union[AgentResponse, str], float]


def _assistant_message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(str(block["text"]))
            elif getattr(block, "text", None) is not None:
                parts.append(str(block.text))
        return "".join(parts) if parts else str(content)
    return str(content)


def _read_user_memory(user_id: str) -> str:
    """Return the user's long-term memory file contents, or empty string if absent."""
    mem_root = settings.user_memories_dir.strip()
    if not mem_root:
        return ""
    mem_path = Path(mem_root) / f"user_{user_id}.md"
    if mem_path.exists():
        try:
            return mem_path.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


# Exam answer records queued to be injected into the next agent call (no round-trip needed).
_pending_exam_context: dict[str, list[str]] = {}


class BaleAgentBridge:
    """Lazily builds the Graphiti deep agent and runs it with per-user thread ids."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agent: Any | None = None

    def _get_agent(self) -> Any:
        with self._lock:
            if self._agent is None:
                from langgraph.checkpoint.memory import MemorySaver

                from app.agent.deep_agent import build_graphiti_deep_agent

                self._agent = build_graphiti_deep_agent(checkpointer=MemorySaver())
            return self._agent

    def add_exam_context(self, user_id: str, entry: str) -> None:
        """Record an exam answer silently — injected into the next agent call."""
        _pending_exam_context.setdefault(user_id, []).append(entry)

    def invoke_reply(self, user_id: str, text: str) -> AgentResult:
        """Run the agent and return (answer, cost_usd)."""
        return self.invoke_reply_with_status(user_id, text)

    def invoke_reply_with_status(
        self,
        user_id: str,
        text: str,
        on_thinking: Callable[[], None] | None = None,
        on_searching: Callable[[], None] | None = None,
        on_got_it: Callable[[], None] | None = None,
    ) -> AgentResult:
        """Run the agent via astream_events and fire status callbacks at key moments."""
        agent = self._get_agent()
        cfg: RunnableConfig = {"configurable": {"thread_id": f"user-{user_id}"}}

        # Prepend long-term memory if available
        memory_contents = _read_user_memory(user_id)
        prefix = f"[حافظه بلندمدت کاربر]\n{memory_contents}\n[پایان حافظه]\n\n" if memory_contents else ""

        # Consume any pending exam context and prepend it
        exam_entries = _pending_exam_context.pop(user_id, [])
        if exam_entries:
            prefix += "[نتایج آزمون این جلسه]\n" + "\n".join(exam_entries) + "\n[پایان نتایج]\n\n"

        user_content: Any = prefix + text if prefix else text

        return asyncio.run(self._stream_agent(agent, cfg, user_content, on_thinking, on_searching, on_got_it))

    async def _stream_agent(
        self,
        agent: Any,
        cfg: RunnableConfig,
        user_content: Any,
        on_thinking: Callable[[], None] | None,
        on_searching: Callable[[], None] | None,
        on_got_it: Callable[[], None] | None,
    ) -> AgentResult:
        thinking_fired = False
        searching_fired = False
        got_it_fired = False
        final_structured: AgentResponse | None = None
        final_content: str = ""
        input_tokens: int = 0
        output_tokens: int = 0

        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": user_content}]},
            config=cfg,
            version="v2",
        ):
            event: StreamEvent
            kind: str = event["event"]

            if not thinking_fired and kind in ("on_chain_start", "on_chat_model_start"):
                thinking_fired = True
                if on_thinking:
                    on_thinking()

            elif kind == "on_tool_start":
                if not searching_fired:
                    searching_fired = True
                    if on_searching:
                        on_searching()

            elif kind == "on_tool_end":
                if not got_it_fired:
                    got_it_fired = True
                    if on_got_it:
                        on_got_it()

            elif kind == "on_chat_model_end":
                raw_output = event.get("data", {}).get("output")
                meta: Any = None
                if raw_output is not None:
                    if hasattr(raw_output, "usage_metadata"):
                        meta = raw_output.usage_metadata  # type: ignore[union-attr]
                    elif isinstance(raw_output, dict):
                        meta = raw_output.get("usage_metadata")
                if meta is not None:
                    if isinstance(meta, dict):
                        input_tokens  += meta.get("input_tokens",  0) or 0
                        output_tokens += meta.get("output_tokens", 0) or 0
                    else:
                        input_tokens  += getattr(meta, "input_tokens",  0) or 0
                        output_tokens += getattr(meta, "output_tokens", 0) or 0

            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict):
                    sr = output.get("structured_response")
                    if isinstance(sr, AgentResponse):
                        final_structured = sr
                    elif isinstance(sr, dict):
                        try:
                            final_structured = AgentResponse(**sr)
                        except Exception:
                            pass
                    elif "messages" in output:
                        msgs = output["messages"]
                        if msgs:
                            try:
                                last = msgs[-1] if isinstance(msgs, list) else list(msgs)[-1]
                            except (TypeError, IndexError):
                                last = None
                            if last is not None:
                                text_candidate = _assistant_message_text(
                                    getattr(last, "content", last)
                                ).strip()
                                if text_candidate:
                                    final_content = text_candidate

        cost_usd = (
            (input_tokens / 1_000_000) * INPUT_COST_PER_1M
            + (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
        )

        if final_structured is not None:
            return final_structured, cost_usd

        # Agent sometimes returns structured data as a plain JSON string — try to parse it.
        if final_content:
            try:
                data = json.loads(final_content)
                if isinstance(data, dict) and "response_type" in data:
                    return AgentResponse(**data), cost_usd
            except Exception:
                pass

        return final_content, cost_usd

    def invoke_welcome(
        self,
        user_id: str,
        first_name: str,
        profile_url: str | None,
    ) -> AgentResult:
        """Run the deep agent for onboarding. Returns (AgentResponse | str, cost_usd)."""
        agent = self._get_agent()
        cfg: RunnableConfig = {"configurable": {"thread_id": f"user-welcome-{user_id}"}}

        prompt = ONBOARDING_PROMPT_TEMPLATE.format(
            first_name=first_name or "دوست",
            photo_line=ONBOARDING_PHOTO_LINE if profile_url else "",
            personality_instruction=PERSONALITY_WITH_PHOTO if profile_url else PERSONALITY_NO_PHOTO,
        )

        if profile_url:
            user_content: Any = [
                {"type": "image_url", "image_url": {"url": profile_url}},
                {"type": "text", "text": prompt},
            ]
        else:
            user_content = prompt

        async def _run() -> AgentResult:
            return await self._stream_agent(agent, cfg, user_content, None, None, None)

        return asyncio.run(_run())

    def save_user_memory(
        self,
        user_id: str,
        first_name: str,
        personality_notes: str,
    ) -> None:
        """Write the user's long-term memory file to USER_MEMORIES_DIR."""
        mem_root = settings.user_memories_dir.strip()
        if not mem_root:
            return
        try:
            path = Path(mem_root) / f"user_{user_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            today = date.today().isoformat()
            content = (
                f"# پروفایل کاربر\n\n"
                f"**نام:** {first_name}\n"
                f"**تاریخ ثبت‌نام:** {today}\n\n"
                f"## شخصیت و سبک یادگیری\n{personality_notes}\n"
            )
            path.write_text(content, encoding="utf-8")
        except Exception:
            pass
