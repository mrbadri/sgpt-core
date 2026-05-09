"""Per-learner disk memory + in-process checkpoint threading for Graphiti deep agent.

This shows how ``build_graphiti_deep_agent(..., user_id=..., user_memories_dir=...)``
maps long-term Markdown (``user_<id>.md`` under a directory root) into the agent
prompt, and how ``MemorySaver`` + a stable ``thread_id`` preserves short-term chat
history for multiple ``ainvoke`` calls within the **same Python process**.

**Prerequisites (same as** ``scripts/graphiti_agent_demo.py`` **)**

- FalkorDB (Redis protocol) reachable via ``FALKOR_*``.
- Chat model env resolved by ``app.agent.deep_agent`` (``AGENT_CHAT_*`` or fallbacks).

**Run from ``backend/``**::

    uv run python examples/graphiti_deep_agent_memory_example.py

**Production checkpoints:** replace ``MemorySaver()`` with Postgres (install
``langgraph-checkpoint-postgres`` per LangGraph docs) and keep ``thread_id`` aligned
with each learner or chat session.

See also: ``examples/graphiti_deep_agent_long_memory_example.py`` for **long-term Markdown
memory only** (no checkpointer). ``scripts/graphiti_agent_demo.py`` for a thinner Falkor
sanity CLI.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from openai import APIConnectionError
from redis.exceptions import ConnectionError as RedisConnectionError

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC = BACKEND_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(BACKEND_ROOT.parent / ".env")

_LLM_CONNECT_HINT = """\
LLM HTTP connection failed (bad host, DNS, or wrong base URL). Fix:
  AGENT_CHAT_MODEL, AGENT_CHAT_API_KEY, AGENT_CHAT_BASE_URL
or fallbacks GRAPHITI_INDEX_LLM_* / GAPGPT_API_KEY / GEMINI_BASE_URL.
Errno 8 / "nodename nor servname" usually means the base URL host is empty or invalid."""

_SAMPLE_MARKDOWN = """# Learner profile (demo)

- Prefers concise answers first, details on request.
- Language: Persian for explanations.
"""


async def main() -> None:
    from app.agent.deep_agent import build_graphiti_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    user_id = "demo_student"

    with tempfile.TemporaryDirectory(prefix="sgpt_memories_") as mem_root:
        mem_dir = Path(mem_root)
        mem_file = mem_dir / f"user_{user_id}.md"
        mem_file.write_text(_SAMPLE_MARKDOWN, encoding="utf-8")

        agent = build_graphiti_deep_agent(
            user_id=user_id,
            user_memories_dir=str(mem_dir),
            checkpointer=MemorySaver(),
        )

        thread_cfg: RunnableConfig = {
            "configurable": {"thread_id": f"graphiti-example-{user_id}"},
        }

        await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "من چه ترجیحی برای زبان پاسخ گفتم؟ یک جمله بگو.",
                    }
                ]
            },
            config=thread_cfg,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "پیام قبلی من یک سوال بود؛ حالا بگو «بله متوجه شدم» اگر تاریخچه را می‌بینی.",
                    }
                ]
            },
            config=thread_cfg,
        )

        last = result["messages"][-1]
        print(getattr(last, "content", last))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except APIConnectionError as e:
        print(f"{e}", file=sys.stderr)
        print(_LLM_CONNECT_HINT, file=sys.stderr)
        raise SystemExit(1) from e
    except RedisConnectionError as e:
        print(
            "Falkor unreachable. Set FALKOR_HOST/FALKOR_PORT/FALKOR_DATABASE.",
            file=sys.stderr,
        )
        raise SystemExit(1) from e
