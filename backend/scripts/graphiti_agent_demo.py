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
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
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


async def run_once(*, query: str, group_ids: str | None) -> None:
    print("run_once: =================")
    print(f"query: {query}")
    print(f"group_ids: {group_ids}")
    from app.agent.deep_agent import build_graphiti_deep_agent
    print("build_graphiti_deep_agent: =================")

    agent = build_graphiti_deep_agent()
    print("agent: =================")
    user_text = query
    if group_ids:
        user_text = f"{query}\n\n(Scope to group_ids: {group_ids})"

    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_text}]})
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
    args = parser.parse_args()
    try:
        print(f"query: {args.query}")
        print(f"group_ids: {args.group_ids}")
        asyncio.run(run_once(query=args.query, group_ids=args.group_ids))
    except RedisConnectionError as e:
        print(f"{e}", file=sys.stderr)
        print(_FALKOR_HINT, file=sys.stderr)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
