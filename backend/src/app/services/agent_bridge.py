"""Bridge between callers (e.g. Bale bot) and the LangGraph deep agent."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from langchain_core.runnables import RunnableConfig


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

    def invoke_reply(self, bale_tid: int, text: str) -> str:
        """Run the agent for a Bale Telegram user id and return the last assistant text."""
        agent = self._get_agent()
        cfg: RunnableConfig = {
            "configurable": {"thread_id": f"bale-{bale_tid}"},
        }

        async def _run() -> dict[str, Any]:
            return await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": text,
                        }
                    ]
                },
                config=cfg,
            )

        result = asyncio.run(_run())
        last = result["messages"][-1]
        return _assistant_message_text(getattr(last, "content", last)).strip()
