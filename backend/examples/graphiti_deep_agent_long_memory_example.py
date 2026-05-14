"""Long-term learner memory only: Markdown on disk injected into the system prompt.

``build_graphiti_deep_agent(..., user_id=..., user_memories_dir=...)`` uses
Deep Agents ``MemoryMiddleware`` behind the scenes: ``user_<id>.md`` is read via
``FilesystemBackend`` and merged into the model context as **persistent** profile
text (outside the sliding chat transcript). This script does **not** use a
checkpointer—that keeps the focus on disk-backed long memory alone.

Contrast with ``graphiti_deep_agent_memory_example.py`` (short-term + ``MemorySaver``
and two conversational turns).

**Prerequisites**

- FalkorDB (``FALKOR_*``).
- Reachable chat API: ``AGENT_CHAT_BASE_URL`` (and key/model) valid — empty or bad host yields
  ``nodename nor servname`` / ``APIConnectionError``.

**Run from ``backend/``**::

    uv run python examples/graphiti_deep_agent_long_memory_example.py
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
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
Errno 8 / "nodename nor servname" usually means the base URL host is empty or invalid."""

# Facts only present in learner markdown — KG search should not contradict them here.
_LONG_MEMORY_MARKDOWN = """# learner_profile

کاربر این آموشیار را برای درس فیزیک دبیرستان استفاده می‌کند.
نام مستعار خودش را برای حافظه بلندمدت «ستاره» انتخاب کرده است.
نقطهٔ ضعف اعلام‌شده: حساب‌دستی گرانیتاسیون؛ ترجیح می‌دهد ابتدا مفهومی توضیح داده شود بعد فرمول.
"""


async def main() -> None:
    from app.agent.deep_agent import build_graphiti_deep_agent

    user_id = "longmem_demo"

    with tempfile.TemporaryDirectory(prefix="sgpt_long_memory_") as mem_root:
        mem_dir = Path(mem_root)
        (mem_dir / f"user_{user_id}.md").write_text(
            _LONG_MEMORY_MARKDOWN.strip() + "\n",
            encoding="utf-8",
        )

        agent = build_graphiti_deep_agent(
            user_id=user_id,
            user_memories_dir=str(mem_dir),
            # Long-memory-only demo — no Postgres / MemorySaver.
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "فقط با تکیه بر «حافظهٔ بلندمدت» خودت (متن کاربر)، "
                            "در سه نکتهٔ خیلی کوتاه بگو: درس موضوعی چیست، نام مستعار چیست، "
                            "و یک ترجیح یادگیری چیست. اگر این اطلاعات در حافظه نیست، بگو ندارم."
                        ),
                    }
                ]
            },
        )

        print("=== answer (expects facts from learner markdown, not Falkor lookup) ===")
        last = result["messages"][-1]
        print(getattr(last, "content", last))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except APIConnectionError as e:
        print(f"{e}", file=sys.stderr)
        print(_LLM_CONNECT_HINT, file=sys.stderr)
        raise SystemExit(1) from e
    except RedisConnectionError:
        print(
            "Falkor unreachable. Set FALKOR_HOST/FALKOR_PORT/FALKOR_DATABASE.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
