"""Bridge between callers (e.g. Bale bot) and the LangGraph deep agent."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from typing import Any, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.schema import StreamEvent

from app.agent.sample import StudentResponse


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

    def invoke_reply(self, bale_tid: int, text: str) -> Union[StudentResponse, str]:
        """Run the agent and return the structured response or last assistant text."""
        return self.invoke_reply_with_status(bale_tid, text)

    def invoke_reply_with_status(
        self,
        bale_tid: int,
        text: str,
        on_thinking: Callable[[], None] | None = None,
        on_searching: Callable[[], None] | None = None,
        on_got_it: Callable[[], None] | None = None,
    ) -> Union[StudentResponse, str]:
        """Run the agent via astream_events and fire status callbacks at key moments.

        Returns a StudentResponse when the agent produces structured output,
        otherwise falls back to the last assistant text string.
        """
        agent = self._get_agent()
        cfg: RunnableConfig = {"configurable": {"thread_id": f"bale-{bale_tid}"}}

        async def _stream() -> Union[StudentResponse, str]:
            thinking_fired = False
            searching_fired = False
            got_it_fired = False
            final_structured: StudentResponse | None = None
            final_content: str = ""

            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": text}]},
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

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        sr = output.get("structured_response")
                        if isinstance(sr, StudentResponse):
                            final_structured = sr
                        elif "messages" in output:
                            msgs = output["messages"]
                            if msgs:
                                last = msgs[-1]
                                text_candidate = _assistant_message_text(
                                    getattr(last, "content", last)
                                ).strip()
                                if text_candidate:
                                    final_content = text_candidate

            return final_structured if final_structured is not None else final_content

        return asyncio.run(_stream())
