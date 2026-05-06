"""HTML → JSON loader using unstructured + Hazm.

``partition_html`` runs language metadata by default (``languages=None`` → ``["auto"]``),
which calls ``langdetect`` on the full document and can be very slow on long Persian
text or look “stuck”. We default to ``languages=[""]`` to skip that step (see unstructured
docs). Override with env ``HTML_LOADER_LANGUAGES`` (comma-separated ISO codes, e.g.
``fas`` or ``auto``).

Run: ``uv run python -m ingestion.loaders.html_loader``
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hazm import Normalizer
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.html import partition_html


def partition_html_to_normalized_chunks(
    html_path: str | Path,
    *,
    languages: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Partition HTML, chunk by title, normalize Persian text; return chunk dicts."""
    html_path = Path(html_path)
    langs = ["fas"] if languages is None else languages

    print("Loading Normalizer...")
    normalizer = Normalizer()

    print("Partitioning HTML file...")
    elements = partition_html(
        filename=str(html_path),
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
        normalized_chunks.append({
            "page_content": normalized_text,
            "metadata": chunk.metadata.to_dict(),
        })
    return normalized_chunks


def load_html_to_json(html_path: str | Path, output_json_path: str | Path) -> None:
    """Partition HTML, chunk by title, normalize Persian text, write chunk JSON."""
    output_json_path = Path(output_json_path)
    normalized_chunks = partition_html_to_normalized_chunks(html_path)

    print("Saving chunks to JSON file...")
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(normalized_chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(normalized_chunks)} chunk(s) to {output_json_path}")


if __name__ == "__main__":
    print("Starting HTML loader...")
    data_dir = Path(__file__).resolve().parent.parent / "data"
    experiment = "exp-g11-bio"
    chapter = "chapter_3"
    load_html_to_json(
        data_dir / "raw" / experiment / "scrape" / chapter / "content.html",
        data_dir / "load" / experiment / chapter / "doc-loader-main-2.json",
    )
