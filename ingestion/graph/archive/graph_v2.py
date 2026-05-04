"""Load split-doc JSON and push episodes to Graphiti."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

from ingestion.config.graphiti import FALKOR_DATABASE

DEFAULT_SPLIT_JSON = (
    Path(__file__).resolve().parent.parent
    / "data/prepare/exp-g11-bio/chapter_3/split-docs-main-75.json"
)


def split_json_path(path: str | Path | None = None) -> Path:
    """JSON file path; ``None`` uses the bundled chapter-3 sample."""
    p = Path(path).expanduser().resolve() if path else DEFAULT_SPLIT_JSON.resolve()
    if not p.is_file():
        raise FileNotFoundError(p)
    return p


def load_docs(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expected a JSON array")
    return data


def _ref_time(meta: dict[str, Any]) -> datetime:
    s = meta.get("last_modified")
    if isinstance(s, str):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            pass
    return datetime.now(UTC)


async def ingest_split_json(
    graphiti: Graphiti,
    path: str | Path | None = None,
    *,
    # FalkorGraphiti maps group_id → Falkor graph name when != driver.database; keep aligned with FALKOR_DATABASE.
    group_id: str = FALKOR_DATABASE,
    setup_db: bool = True,
    limit: int | None = None,
) -> int:
    """One episode per non-empty ``page_content``; returns how many were added."""
    path = split_json_path(path)
    rows = load_docs(path)
    if setup_db:
        await graphiti.build_indices_and_constraints()

    stem = path.stem
    n = 0
    for i, row in enumerate(rows):
        if limit is not None and n >= limit:
            break
        text = row.get("page_content")
        if not isinstance(text, str) or not text.strip():
            continue
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        await graphiti.add_episode(
            name=f"{stem}-{i:05d}",
            episode_body=text.strip(),
            source_description=f"{stem} #{i} ({meta.get('filename', '?')})",
            reference_time=_ref_time(meta),
            source=EpisodeType.text,
            group_id=group_id,
        )
        n += 1
    return n


async def main() -> None:
    from ingestion.config.graphiti import create_graphiti

    g = create_graphiti()
    try:
        count = await ingest_split_json(g)
        print(f"Imported {count} episodes")
    finally:
        await g.close()


if __name__ == "__main__":
    asyncio.run(main())
