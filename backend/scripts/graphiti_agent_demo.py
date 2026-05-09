"""Run the Graphiti deep agent once from the terminal (notebook demo as a script).

Requires LLM/API env (``AGENT_CHAT_*`` or fallbacks in ``app.agent.deep_agent``) plus
Graphiti-backed **FalkorDB over Redis**. Defaults: ``127.0.0.1:6379``. Override::

    FALKOR_HOST=
    FALKOR_PORT=
    FALKOR_DATABASE=

(see repo ``.env.example``). Neo4j ``NEO4J_*`` vars are **not** used by this harness.

Run from ``backend/``::

    uv run python scripts/graphiti_agent_demo.py
    uv run python scripts/graphiti_agent_demo.py --query "سلام"
    uv run python scripts/graphiti_agent_demo.py --group-ids my_group,g2
"""

from __future__ import annotations

import argparse
from typing import cast
import asyncio
import sys
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

_FALKOR_HINT = """\
FalkorDB (Redis protocol) unreachable. Start Falkor locally or point env at your instance:
  FALKOR_HOST, FALKOR_PORT (default 127.0.0.1:6379), FALKOR_DATABASE
See app.config.graphiti.GraphitiSettings / repo .env.example."""

_LLM_CONNECT_HINT = """\
LLM HTTP connection failed (bad host, DNS, or wrong base URL). Fix:
  AGENT_CHAT_MODEL, AGENT_CHAT_API_KEY, AGENT_CHAT_BASE_URL
or fallbacks GRAPHITI_INDEX_LLM_* / GAPGPT_API_KEY / GEMINI_BASE_URL.
Errno 8 / "nodename nor servname" usually means the base URL host is empty or invalid."""


async def run_once(
    *,
    query: str,
    group_ids: str | None,
    user_id: str | None = None,
) -> None:
    print("run_once: =================")
    print(f"query: {query}")
    print(f"group_ids: {group_ids}")
    from app.agent.deep_agent import build_graphiti_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    print("build_graphiti_deep_agent: =================")
    # Per-learner disk memory: export USER_MEMORIES_DIR=/path/to/memories and optional --user-id
    # (creates/reads USER_MEMORIES_DIR/user_<id>.md via FilesystemBackend).
    agent = build_graphiti_deep_agent(
        user_id=user_id,
        checkpointer=MemorySaver(),
    )
    print("agent: =================")
    user_text = query
    if group_ids:
        user_text = f"{query}\n\n(Scope to group_ids: {group_ids})"

    cfg = cast(
        RunnableConfig,
        {"configurable": {"thread_id": f"user-{user_id}" if user_id else "demo-thread"}},
    )
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=cfg,
    )
    print("result: =================")
    print(result)
    last_msg = result["messages"][-1]
    print(getattr(last_msg, "content", last_msg))


def main() -> None:
    print("===== RUN ======")
    parser = argparse.ArgumentParser(description="Graphiti deep agent one-shot CLI")
    parser.add_argument(
        "--query",
        "-q",
        default="""تمام پیام های حسی در ساختاری از مغز که بالای ساختار تنظیم کننده دما قرار دارد گرد هم می آیند و پردازش اولیه می شوند.

درست یا نادرست بودن جمله رو مشخص کن""",
        help="User message to send to the agent",
    )
    parser.add_argument(
        "--group-ids",
        default=None,
        metavar="IDS",
        help='Optional Falkor-style scope (e.g. "g1,g2")',
    )
    parser.add_argument(
        "--user-id",
        default=None,
        metavar="ID",
        help="Load long-term memory from USER_MEMORIES_DIR/user_<ID>.md (set USER_MEMORIES_DIR)",
    )
    args = parser.parse_args()
    try:
        print(f"query: {args.query}")
        print(f"group_ids: {args.group_ids}")
        asyncio.run(
            run_once(query=args.query, group_ids=args.group_ids, user_id=args.user_id)
        )
    except APIConnectionError as e:
        print(f"{e}", file=sys.stderr)
        print(_LLM_CONNECT_HINT, file=sys.stderr)
        raise SystemExit(1) from e
    except RedisConnectionError as e:
        print(f"{e}", file=sys.stderr)
        print(_FALKOR_HINT, file=sys.stderr)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
