"""Bulk HTML → JSON: walk a scrape root, load each subfolder's ``content.html``, enrich metadata from folder slug.

Folder name pattern (parsed into metadata):
    ``{major}-g{NN}-{subject}-chapter{CH}-section{SEC}-{publish_year}``
Example: ``exp-g11-bio-chapter1-section0-1404`` → ``major=exp``, ``grade=11``, ``publish_year=1404``.

Run: ``uv run python -m ingestion.loaders.bulk_html_loader --scrape-root ... --out ...``


 uv run python -m ingestion.loaders.bulk_html_loader \
  --scrape-root ingestion/data/raw/exp-g11-bio/scrape \
  --out ingestion/data/load/exp-g11-bio/bulk
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from ingestion.loaders.html_loader import partition_html_to_normalized_chunks

_SLUG_RE = re.compile(
    r"^(?P<major>[^-]+)-(?P<grade>g\d+)-(?P<subject>[^-]+)-"
    r"chapter(?P<chapter>\d+)-section(?P<section>\d+)-(?P<publish_year>\d+)$"
)


def scrape_folder_slug_metadata(folder_name: str) -> dict[str, Any]:
    """Parse scrape subfolder name; on failure return ``scrape_folder`` + ``slug_parse_ok=False``."""
    m = _SLUG_RE.fullmatch(folder_name)
    base: dict[str, Any] = {"scrape_folder": folder_name}
    if not m:
        base["slug_parse_ok"] = False
        return base
    base["slug_parse_ok"] = True
    base["major"] = m.group("major")
    base["grade"] = int(m.group("grade")[1:])
    base["subject"] = m.group("subject")
    base["chapter"] = int(m.group("chapter"))
    base["section"] = int(m.group("section"))
    base["publish_year"] = int(m.group("publish_year"))
    return base


def bulk_load_scrape_root(
    scrape_root: Path,
    output_dir: Path,
    *,
    html_filename: str = "content.html",
) -> None:
    """For each immediate subfolder containing ``html_filename``, write ``{slug}.json`` under ``output_dir``."""
    scrape_root = scrape_root.resolve()
    if not scrape_root.is_dir():
        raise NotADirectoryError(f"scrape_root is not a directory: {scrape_root}")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    subdirs = sorted(p for p in scrape_root.iterdir() if p.is_dir())
    processed = 0
    for child in subdirs:
        html_path = child / html_filename
        if not html_path.is_file():
            continue
        slug = child.name
        print(f"\n--- {slug} ---")
        extra_meta = scrape_folder_slug_metadata(slug)
        if not extra_meta.get("slug_parse_ok", False):
            print(f"Warning: folder name did not match expected slug pattern: {slug!r}")

        chunks = partition_html_to_normalized_chunks(html_path)
        for item in chunks:
            item.setdefault("metadata", {})
            item["metadata"].update(extra_meta)

        out_path = output_dir / f"{slug}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(chunks)} chunk(s) to {out_path}")
        processed += 1

    print(f"\nDone. Processed {processed} folder(s) under {scrape_root}")


def _main() -> None:
    parser = argparse.ArgumentParser(description="Bulk-load HTML from scrape subfolders to JSON.")
    parser.add_argument(
        "--scrape-root",
        type=Path,
        required=True,
        help="Directory whose immediate children are lesson folders (each with content.html).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Directory to write one JSON file per slug (folder name).",
    )
    parser.add_argument(
        "--html-filename",
        default="content.html",
        help="HTML file name inside each subfolder (default: content.html).",
    )
    args = parser.parse_args()
    bulk_load_scrape_root(
        args.scrape_root,
        args.out,
        html_filename=args.html_filename,
    )


if __name__ == "__main__":
    _main()
