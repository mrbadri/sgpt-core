"""Markdown → JSON loader using unstructured + Hazm.

``partition_md`` converts Markdown to HTML then calls ``partition_html``. Language
metadata behaves like HTML partitioning; we default to ``languages=["fas"]`` for
parity with ``html_loader`` (override via the ``languages`` argument).

Run:

- Default sample: ``uv run python -m ingestion.loaders.markdown_loader``
- Custom paths: ``uv run python -m ingestion.loaders.markdown_loader --md …/content.md --out …/out.json``
- Lesson slug (same fields as bulk HTML): ``… --slug exp-g11-bio-chapter1-section1-1404``


✗ uv run python -m ingestion.loaders.markdown_loader \
  --md ingestion/data/raw/exp-g11-bio/tmp/exp-g11-bio-chapter8-section3-1404/content.md \ 
  --out ingestion/data/load/exp-g11-bio/single/exp-g11-bio-chapter8-section3-1404.json \
  --slug exp-g11-bio-chapter8-section3-1404
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hazm import Normalizer
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.md import partition_md

from ingestion.loaders.bulk_html_loader import scrape_folder_slug_metadata


def partition_md_to_normalized_chunks(
    md_path: str | Path,
    *,
    languages: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Partition Markdown, chunk by title, normalize Persian text; return chunk dicts."""
    md_path = Path(md_path)
    langs = ["fas"] if languages is None else languages

    print("Loading Normalizer...")
    normalizer = Normalizer()

    print("Partitioning Markdown file...")
    elements = partition_md(
        filename=str(md_path),
        languages=langs,
    )
    print(f"Extracted {len(elements)} element(s).")

    print("Chunking elements...")
    chunks = chunk_by_title(
        elements,
        combine_text_under_n_chars=300,
        max_characters=2000,
        new_after_n_chars=1500,
        overlap=200,
    )
    print(f"Created {len(chunks)} chunk(s).")

    print("Normalizing text...")
    normalized_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        normalized_text = normalizer.normalize(chunk.text)
        meta = chunk.metadata.to_dict()
        if extra_metadata:
            meta = {**meta, **extra_metadata}
        normalized_chunks.append({
            "page_content": normalized_text,
            "metadata": meta,
        })
    return normalized_chunks


def load_md_to_json(
    md_path: str | Path,
    output_json_path: str | Path,
    *,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Partition Markdown, chunk by title, normalize Persian text, write chunk JSON."""
    output_json_path = Path(output_json_path)
    normalized_chunks = partition_md_to_normalized_chunks(
        md_path,
        extra_metadata=extra_metadata,
    )

    print("Saving chunks to JSON file...")
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(normalized_chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(normalized_chunks)} chunk(s) to {output_json_path}")


def _main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    experiment = "exp-g11-bio"
    default_slug = "exp-g11-bio-chapter9-section0-1404"
    default_md = data_dir / "raw" / experiment / "scrape" / default_slug / "content.md"
    default_out = data_dir / "load" / experiment / "scrape" / default_slug / "doc-loader-md.json"

    parser = argparse.ArgumentParser(description="Load one Markdown file → chunked JSON.")
    parser.add_argument(
        "--md",
        type=Path,
        default=default_md,
        help=f"Path to content.md (default: repo sample under scrape/{default_slug}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=default_out,
        help="Output JSON path (default: mirrors default --md under data/load/…).",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help=(
            "Lesson folder name parsed into metadata (major, grade, subject, chapter, section, "
            "publish_year); same pattern as bulk_html_loader scrape subfolders."
        ),
    )
    args = parser.parse_args()
    md_path = args.md.resolve()
    if not md_path.is_file():
        raise FileNotFoundError(
            f"Markdown file not found: {md_path}\n"
            "Pass --md to your content.md (e.g. under raw/…/tmp/<lesson-slug>/)."
        )
    extra_meta: dict[str, Any] | None = None
    if args.slug:
        extra_meta = scrape_folder_slug_metadata(args.slug.strip())
        if not extra_meta.get("slug_parse_ok", False):
            print(f"Warning: --slug did not match expected pattern: {args.slug!r}")

    print("Starting Markdown loader...")
    load_md_to_json(md_path, args.out.resolve(), extra_metadata=extra_meta)


if __name__ == "__main__":
    _main()
