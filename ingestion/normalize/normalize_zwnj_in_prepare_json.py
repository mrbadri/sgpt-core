"""Normalize Persian text in prepare JSON arrays (Hazm + ZWNJ rules).

Every **string value** in each row object is normalized recursively (including
``page_content``, ``metadata``, nested lists, etc.). JSON keys are left unchanged.
Each string is passed through Hazm ``Normalizer()`` first (same defaults as
``ingestion.loaders.html_loader``).

After Hazm, ``U+06C0`` (``ۀ``, heh with yeh above) is replaced with plain ``ه`` (``U+0647``)
everywhere.

Then the previous ZWNJ logic runs unchanged: ``U+200C`` becomes ASCII space
except inside protected patterns (می‌ / ثبت‌شده / …). Plural
``…‌ها`` / ``…‌های`` / ``…‌هایی`` … are opened with spaces and the gap before those
suffixes is widened to **two** spaces (``یاخته‌های`` → ``یاخته  های``).

**Order matters:** Hazm, then ``ۀ``→``ه``, then the ZWNJ pass. Running Hazm after
ZWNJ would re-glue plural suffixes with ZWNJ and undo the widened gap.

Usage::

    uv run python ingestion/data/prepare/normalize_zwnj_in_prepare_json.py \\
        ingestion/data/prepare/exp-g11-bio/exp-g11-bio-1404.json \\
        -o ingestion/data/prepare/exp-g11-bio/exp-g11-bio-1404.spaced.json

Use ``--indent 0`` for a single-line (compact) file; default is ``4`` (more open layout than typical ``2``-space JSON).

Or from code::

    from ingestion.data.prepare.normalize_zwnj_in_prepare_json import (
        normalize_page_content_zwnj,
        transform_prepare_json_rows,
    )
"""

from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Any, cast

from hazm import Normalizer

ZWNJ = "\u200c"
# Shared with ``html_loader.partition_html_to_normalized_chunks`` (default kwargs).
_HAZM_NORMALIZER = Normalizer()
# Persian / Arabic letters + Persian digits + common presentation forms used in textbooks
_AR = r"\u0600-\u06FF\u0660-\u0669\u06F0-\u06F9\u067E\u0686\u0698\u06A9\u06AF"
_TOKEN_END = r'(?=[\s,.،؛:!?"\'()«»\[\]{}⟨⟩*\u200c\u200d\n\u00a0]|$)'

# Suffixes still joined with ZWNJ (not plural ها / های / هایی / … — those are spaced).
_SUFFIX_NON_PLURAL = (
    r"تر|ترین|"
    r"ای|ام|ات|اش|مان|تان|شان|"
    r"ان|ین|"
    r"گاه|گر|وار|"
    r"دار|آمیز"
)
_PARTICIPLE = (
    r"شده|شدۀ|شوند|شدند|نشده|"
    r"مانده|آمده|آورده|داده|کرده|گفته|گرفته|زده|"
    r"افتاده|ستاده|گذشته|بوده|نموده|بسته|"
    r"نده|ننده|اند|نده‌اند|ده‌اند"
)
_PROTECT_RAW: tuple[str, ...] = (
    # می‌کنند، نمی‌رود، بی‌تفاوت، فراورده، فروش…
    rf"(?:می|نمی|بی|فرا|فرو){ZWNJ}[{_AR}]+",
    # گفت‌وگو (دو نیم‌فاصله پیرامون «و»)
    rf"[{_AR}]{{2,}}{ZWNJ}و{ZWNJ}[{_AR}]{{2,}}",
    # سوخت‌وساز و امثال (یک نیم‌فاصله قبل از «و…»)
    rf"[{_AR}]{{2,}}{ZWNJ}و[{_AR}]{{2,}}{_TOKEN_END}",
    # واژه‌شناسی و مشابه
    rf"[{_AR}]{{2,}}{ZWNJ}شناسی{_TOKEN_END}",
    # تحریک‌پذیر، تحریک‌پذیرند، … (پسوندهای حالی/شنی)
    rf"[{_AR}]{{2,}}{ZWNJ}پذیر[\u0600-\u06FF]{{0,4}}{_TOKEN_END}",
    # عایق‌بندی، …
    rf"[{_AR}]{{2,}}{ZWNJ}بندی{_TOKEN_END}",
    # چسب‌های غیرجمع (رشته‌ای، …) — جمع ‌ها/های/هایی… عمداً حفاظت نمی‌شود
    rf"[{_AR}]{{2,}}{ZWNJ}(?:{_SUFFIX_NON_PLURAL}){_TOKEN_END}",
    # اندازه‌گیری، …
    rf"[{_AR}]{{2,}}ه{ZWNJ}گیری{_TOKEN_END}",
    # ریشه + ‌ + مصدر/وصفِ پرتکرار در زیست
    rf"[{_AR}]{{2,}}{ZWNJ}(?:{_PARTICIPLE}){_TOKEN_END}",
    # میلی‌ولت و مشابه
    rf"[{_AR}]{{2,}}{ZWNJ}ولت{_TOKEN_END}",
    # …ه‌… که جمع نیست (جلوگیری از بلعیدن «یاخته‌های»: بعد از ‌ نباید فوراً ها/های/هایی باشد)
    rf"[{_AR}]{{2,}}ه{ZWNJ}(?!هایی)(?!های)(?!ها)([{_AR}]{{2,}}){_TOKEN_END}",
    # درون‌یاخته و امثال (…‌ی…)
    rf"[{_AR}]{{2,}}{ZWNJ}ی[{_AR}]{{3,}}{_TOKEN_END}",
)

_PROTECT_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.UNICODE) for p in _PROTECT_RAW
)

# After ZWNJ→space: ``کلمه های`` / ``کلمه هایی`` → ``کلمه  های`` (two spaces).
_PLURAL_SUFFIXES = r"ها|های|هایی|هایم|هایت|هایش|هایمان|هایتان|هایشان"
_WIDEN_PLURAL_GAP = re.compile(
    rf"([{_AR}]{{2,}}) ({_PLURAL_SUFFIXES})(?={_TOKEN_END})",
    re.UNICODE,
)

# U+06C0 ARABIC LETTER HEH WITH YEH ABOVE → plain heh (Persian «ۀ» → «ه»).
_HEH_WITH_YEH_ABOVE = "\u06c0"
_ARABIC_LETTER_HEH = "\u0647"


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    intervals.sort(key=lambda x: (x[0], x[1]))
    out = [list(intervals[0])]
    for s, e in intervals[1:]:
        last = out[-1]
        if s <= last[1]:
            last[1] = max(last[1], e)
        else:
            out.append([s, e])
    return [(a[0], a[1]) for a in out]


def _mask_protected_spans(text: str, patterns: tuple[re.Pattern[str], ...]) -> tuple[str, dict[str, str]]:
    """Replace whole protected spans with placeholders so inner ZWNJ is untouched by blanket rules."""

    segments: list[tuple[int, int]] = []
    for pat in patterns:
        for m in pat.finditer(text):
            segments.append((m.start(), m.end()))
    merged = _merge_intervals(segments)
    if not merged:
        return text, {}
    table: dict[str, str] = {}
    pieces: list[str] = []
    pos = 0
    for s, e in merged:
        if pos < s:
            pieces.append(text[pos:s])
        token = f"__ZWNJPROT_{uuid.uuid4().hex}__"
        table[token] = text[s:e]
        pieces.append(token)
        pos = e
    if pos < len(text):
        pieces.append(text[pos:])
    return "".join(pieces), table


def normalize_page_content_zwnj(text: str) -> str:
    """Run Hazm ``Normalizer``, then mask/unmask ZWNJ (unchanged rules)."""

    text = _HAZM_NORMALIZER.normalize(text)
    text = text.replace(_HEH_WITH_YEH_ABOVE, _ARABIC_LETTER_HEH)
    if ZWNJ not in text:
        return text
    masked, ph = _mask_protected_spans(text, _PROTECT_PATTERNS)
    masked = masked.replace(ZWNJ, " ")
    for k, v in ph.items():
        masked = masked.replace(k, v)
    return _WIDEN_PLURAL_GAP.sub(r"\1  \2", masked)


def _deep_normalize_strings(obj: Any) -> tuple[Any, bool]:
    """Return a deep copy with every str passed through ``normalize_page_content_zwnj``."""

    if isinstance(obj, str):
        n = normalize_page_content_zwnj(obj)
        return n, n != obj
    if isinstance(obj, list):
        changed = False
        out: list[Any] = []
        for item in obj:
            new_item, c = _deep_normalize_strings(item)
            out.append(new_item)
            changed |= c
        return out, changed
    if isinstance(obj, dict):
        changed = False
        out: dict[str, Any] = {}
        for k, v in obj.items():
            new_v, c = _deep_normalize_strings(v)
            out[k] = new_v
            changed |= c
        return out, changed
    return obj, False


def transform_prepare_json_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    changed = 0
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        new_row, row_changed = _deep_normalize_strings(row)
        if row_changed:
            changed += 1
        out.append(cast(dict[str, Any], new_row))
    return out, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize Persian text in prepare JSON (all string values per row).",
    )
    parser.add_argument("input", type=Path, help="Input JSON array file (UTF-8).")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output JSON path (will not overwrite input unless equal).",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=4,
        help="JSON pretty indent (default: 4). Use 0 for one-line compact output.",
    )
    args = parser.parse_args()
    inp: Path = args.input.expanduser().resolve()
    outp: Path = args.output.expanduser().resolve()
    if not inp.is_file():
        raise SystemExit(f"not a file: {inp}")

    raw = inp.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("expected top-level JSON array")

    new_rows, n_changed = transform_prepare_json_rows(data)
    indent = None if args.indent == 0 else args.indent
    text_out = json.dumps(new_rows, ensure_ascii=False, indent=indent)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(text_out + ("\n" if text_out and not text_out.endswith("\n") else ""), encoding="utf-8")
    print(f"wrote {outp} ({n_changed} row(s) with at least one string changed)")


if __name__ == "__main__":
    main()
