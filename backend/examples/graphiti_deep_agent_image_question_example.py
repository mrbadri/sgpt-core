"""Ask the Graphiti deep agent a question that arrives as an **image** (OCR + answer).

Uses a vision-capable chat model (e.g. ``gpt-4o`` via ``AGENT_CHAT_MODEL``): the user
message is a ``HumanMessage`` with ``text`` + ``image_url`` (base64 data URL). The agent
may call ``search_knowledge_graph`` when course context from the graph helps.

**Prerequisites**

- Same as other examples: valid ``AGENT_CHAT_*`` (especially a **vision** model),
  Falkor (``FALKOR_*``).
- Sample asset: ``examples/question.png`` (or pass ``--image``).

**Run from ``backend/``**::

    uv run python examples/graphiti_deep_agent_image_question_example.py
    uv run python examples/graphiti_deep_agent_image_question_example.py --image path/to/screenshot.png

If the OpenAI-compatible endpoint does not support image inputs, you will get a 4xx /
validation error from the API — switch to a multimodal model or a provider that
implements the vision content blocks.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import mimetypes
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from openai import APIConnectionError
from redis.exceptions import ConnectionError as RedisConnectionError

BACKEND_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = Path(__file__).resolve().parent
SRC = BACKEND_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(BACKEND_ROOT.parent / ".env")

DEFAULT_IMAGE = EXAMPLES_DIR / "question.png"

_LLM_CONNECT_HINT = """\
LLM HTTP connection failed. For **image** turns you need a vision-capable model (e.g. gpt-4o)
and a working AGENT_CHAT_BASE_URL. See other examples' hints for env names."""


def _guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".gif":
        return "image/gif"
    if suffix == ".webp":
        return "image/webp"
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "image/png"


def _data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    mime = _guess_mime(path)
    return f"data:{mime};base64,{b64}"


async def main(*, image_path: Path, extra_instruction: str | None) -> None:
    from app.agent.deep_agent import build_graphiti_deep_agent

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    preamble = (
        "این پیام شامل یک تصویر است (مثلاً اسکرین‌شات سوال کتاب درسی).\n"
        "۱) ابتدا متن/سوال را از تصویر استخراج کن (در صورت خوانایی پایین، بهترین حدس را بگو).\n"
        "۲) سپس طبق نقش دستیار آموزشی و در صورت نیاز با ابزار جست‌وجوی گراف، پاسخ دقیق و کوتاه بده.\n"
        "زبان پاسخ را مانند زبان سوال یا فارسی کتاب درسی نگه دار.\n"
    )
    if extra_instruction:
        preamble += f"\n{extra_instruction.strip()}\n"

    url = _data_url(image_path)
    human = HumanMessage(
        content=[
            {"type": "text", "text": preamble},
            {"type": "image_url", "image_url": {"url": url}},
        ],
    )

    agent = build_graphiti_deep_agent()
    result = await agent.ainvoke({"messages": [human]})
    last = result["messages"][-1]
    print(getattr(last, "content", last))


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Send an image question to the Graphiti deep agent (vision + optional KG)",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=Path,
        default=DEFAULT_IMAGE,
        help=f"Image file path (default: {DEFAULT_IMAGE.name} next to this script)",
    )
    parser.add_argument(
        "--note",
        "-n",
        default=None,
        help="Optional extra Persian/English instruction appended to the OCR prompt",
    )
    args = parser.parse_args()
    try:
        asyncio.run(main(image_path=args.image.resolve(), extra_instruction=args.note))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        raise SystemExit(2) from e
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


if __name__ == "__main__":
    _cli()
