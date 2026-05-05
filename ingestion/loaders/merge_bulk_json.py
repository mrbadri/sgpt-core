"""Merge per-lesson bulk chunk JSON files into one JSON array.

Each input file must be a JSON list of ``{ "page_content", "metadata" }`` objects
(as produced by ``bulk_html_loader``). Files are merged in slug order (chapter,
section, publish_year when the stem matches the scrape slug pattern).

Run:

``uv run python -m ingestion.loaders.merge_bulk_json --in ingestion/data/load/exp-g11-bio/bulk --out ingestion/data/load/exp-g11-bio/all-lessons.json``

Optional: ``--annotate-source`` adds ``bulk_json_file`` to each chunk's metadata.



uv run python -m ingestion.loaders.merge_bulk_json \
  --in ingestion/data/load/exp-g11-bio/bulk \
  --out ingestion/data/load/exp-g11-bio/exp-g11-bio-all-chapters.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ingestion.loaders.bulk_html_loader import scrape_folder_slug_metadata


def _json_sort_key(path: Path) -> tuple[Any, ...]:
    stem = path.stem
    meta = scrape_folder_slug_metadata(stem)
    if meta.get("slug_parse_ok"):
        return (
            meta["chapter"],
            meta["section"],
            meta["publish_year"],
            meta["grade"],
            stem,
        )
    return (9999, 9999, 9999, 9999, stem)


def merge_bulk_json_dir(
    input_dir: Path,
    output_path: Path,
    *,
    annotate_source: bool = False,
    pattern: str = "*.json",
) -> list[dict[str, Any]]:
    """Load every ``pattern`` JSON under ``input_dir`` (non-recursive), concat lists, write ``output_path``."""
    input_dir = input_dir.resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"input_dir is not a directory: {input_dir}")

    paths = sorted(input_dir.glob(pattern), key=_json_sort_key)
    merged: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array in {path}, got {type(data).__name__}")
        if annotate_source:
            label = path.name
            for item in data:
                if isinstance(item, dict):
                    item.setdefault("metadata", {})
                    if isinstance(item["metadata"], dict):
                        item["metadata"]["bulk_json_file"] = label
        merged.extend(data)
        print(f"Merged {len(data)} chunk(s) from {path.name}")

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(merged)} chunk(s) total → {output_path}")
    return merged


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge bulk lesson JSON files (each a chunk list) into one JSON file.",
    )
    parser.add_argument(
        "--in",
        dest="input_dir",
        type=Path,
        required=True,
        help="Folder containing per-lesson *.json files (e.g. bulk_html_loader --out).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON path (single array of all chunks).",
    )
    parser.add_argument(
        "--annotate-source",
        action="store_true",
        help='If set, each chunk metadata gets "bulk_json_file" with the source filename.',
    )
    parser.add_argument(
        "--pattern",
        default="*.json",
        help="Glob relative to input dir (default: *.json).",
    )
    args = parser.parse_args()
    merge_bulk_json_dir(
        args.input_dir,
        args.out,
        annotate_source=args.annotate_source,
        pattern=args.pattern,
    )


if __name__ == "__main__":
    _main()
