"""Load split-doc JSON and push episodes to Graphiti.

Optional curriculum fields from each row's ``metadata`` are written on ``:Episodic`` after each
successful ``add_episode``. Textbook scaffolding (``:Book``, ``:Chapter``, ``:Section``) and linkage
``:Section`` -[:SECTION_HAS_EPISODE]-> ``:Episodic`` (by default) mirrors ``exp_g11_bio_1404_metadata``.

Entity and relationship extraction uses Graphiti's built-in prompts unless you opt in via
``custom_extraction_instructions``, ``include_domain_extraction_base``, or the
``GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS`` environment variable.

Optionally an ``Episode`` secondary label is applied when ``add_episode_label`` is true.

Structural links default to ``SECTION_HAS_EPISODE`` (not Saga ``HAS_EPISODE``).

**Several episodics often share one Section** (same ``chapter``/``section`` metadata after semantic
split). Avoid ``ORDER BY e.name`` when choosing one episode lexicographically: order is **not numeric**
(for example ``…-00021`` sorts before ``…-00004``). Use ``ORDER BY e.json_row_index``
(SET during ingest), or ``MATCH … WHERE e.name = $exact``.

List episodic rows: ``MATCH (e:Episodic) WHERE e.group_id = $g RETURN DISTINCT e``.

Set ``INGEST_TRACE_TIMING=1`` (or ``true`` / ``yes`` / ``y`` / ``on``) to log per-phase wall times during
``ingest_split_json`` (build indices, resume query, each ``add_episode`` vs metadata vs textbook links).

Set ``INGEST_GRAPHITI_TRACE=1`` to log nested Graphiti spans inside each ``add_episode`` (especially each
``llm.generate`` call and ``prompt.name``). Add ``INGEST_GRAPHITI_TRACE_VERBOSE=1`` for all span attributes.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.driver.driver import GraphDriver
from graphiti_core.llm_client.errors import RateLimitError as GraphitiRateLimitError
from graphiti_core.nodes import EpisodeType

from config.falkordb import FALKOR_DATABASE

# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------
_RATE_LIMIT_INITIAL_WAIT_S = float(os.environ.get("INGEST_RATE_LIMIT_WAIT_S", "60"))
_RATE_LIMIT_MAX_RETRIES = int(os.environ.get("INGEST_RATE_LIMIT_MAX_RETRIES", "5"))


async def _add_episode_with_retry(graphiti: Graphiti, **kwargs):
    """Call graphiti.add_episode with exponential back-off on RateLimitError."""
    wait = _RATE_LIMIT_INITIAL_WAIT_S
    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 1):
        try:
            return await graphiti.add_episode(**kwargs)
        except GraphitiRateLimitError as exc:
            if attempt == _RATE_LIMIT_MAX_RETRIES:
                raise
            logging.getLogger(__name__).warning(
                "rate_limit attempt=%s/%s waiting=%.0fs episode_name=%s",
                attempt,
                _RATE_LIMIT_MAX_RETRIES,
                wait,
                kwargs.get("name", "?"),
            )
            await asyncio.sleep(wait)
            wait = min(wait * 2, 600)


def _load_textbook_structure():
    """Load ``textbook_structure`` as a submodule of the ``graph`` package, or by path.

    Running ``python graph/graph.py`` puts ``graph/graph.py`` on ``sys.path`` as top-level ``graph`` —
    then ``from graph.textbook_structure …`` fails (``graph`` is a module file, not a package).
    Fallback loads the sibling ``textbook_structure.py`` explicitly.
    """

    try:
        from graph.textbook_structure import (
            ensure_textbook_structure_skeleton as _ensure_skel,
            label_episodic_as_episode as _label_episode,
            link_section_has_episode as _link_sec,
            resolve_structural_source as _resolve_src,
        )
    except (ImportError, ModuleNotFoundError):
        tp = Path(__file__).resolve().parent / "textbook_structure.py"
        spec = importlib.util.spec_from_file_location("_sgpt_graph_textbook_structure", tp)
        if spec is None or spec.loader is None:
            raise
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _ensure_skel = mod.ensure_textbook_structure_skeleton
        _label_episode = mod.label_episodic_as_episode
        _link_sec = mod.link_section_has_episode
        _resolve_src = mod.resolve_structural_source

    return _ensure_skel, _label_episode, _link_sec, _resolve_src


(
    ensure_textbook_structure_skeleton,
    label_episodic_as_episode,
    link_section_has_episode,
    resolve_structural_source,
) = _load_textbook_structure()

# ثابت تا با اجرای مستقیم‌ی فایل (__main__) هم همان هندلر رنگی گیرد.
logger = logging.getLogger("ingestion.graph.graph")


def _ingest_trace_timing_enabled() -> bool:
    v = (os.environ.get("INGEST_TRACE_TIMING") or "").strip().lower()
    return v in ("1", "true", "yes", "y", "on")

DEFAULT_SPLIT_JSON = (
    Path(__file__).resolve().parent.parent
    / "data/normalize/exp-g11-bio/exp-g11-bio-1404.json"
)

# Appended when ``prepend_episode_source`` and ``structural_extraction_guard`` are both true
# («منبع:» preface plus other textbook scaffolding the model should not treat as biology concepts).
STRUCTURAL_EXTRACTION_GUARD_EN = (
    "\n\nSTRUCTURAL SCAFFOLDING (Persian textbook):\n"
    "A) «منبع:» HEADER (narrow): Use **only** when the TEXT begins with one or more lines whose **first line** "
    "starts with «منبع:».\n"
    "- Treat **only**: that first «منبع:» line, plus any following lines **until and including the first "
    "completely blank line**, as catalog/source scaffolding — **not** substantive lesson content.\n"
    "- Do **not** extract entities, concepts, facts, edges, or relationship endpoints from **that header block alone**.\n"
    "- **Everything after** that blank line separator is normal curriculum text: apply the usual Graphiti extraction "
    "rules there in full (entities and inter-entity facts as appropriate).\n"
    "- If there is **no** «منبع:» prefix at the top, skip subsection A only.\n"
    "B) FIGURE / IMAGE / CHART CALLOUTS (anywhere): Do **not** mint entities (or use as sole relationship endpoints) "
    "for bare pointers like «شکل ۱», «تصویر ۲», «نمودار ۱», or the same with Western digits—those are navigational "
    "labels, not biology concepts.\n"
    "- Never generalize «do not extract» to Persian body paragraphs that are not part of subsection A's header block."
)


# Used when ``include_domain_extraction_base`` is true and ``GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS`` is unset.
DEFAULT_CUSTOM_EXTRACTION_INSTRUCTIONS_EN = (
    "Persian (Farsi) high-school biology: extract the episode's biological concepts and substantive terms "
    "(ideas and vocabulary likely to show up again—other chapters, exams). "
    "Try to surface at least one defensible biology concept per episode whenever the passage supports it; "
    "more on-topic biology is better, but only what the text actually justifies—no padding or generic filler.\n"
    "PERSIAN SPELLING (STRICT): entity names must match the episode verbatim, including ZWNJ (U+200C)—never normalize it away. "
    "ZWNJ often sits before plural «های»/«ها» or ezafe «ی»; do not glue stem+suffix (BAD «یاختههای»; GOOD «یاخته‌های» if the source shows the half-space). "
    "If the source has no ZWNJ there, still avoid invented merges—use the shortest exact substring from the text."
)


def _domain_extraction_base_text(*, include_domain_base: bool) -> str:
    """Biology/Persian hints: env ``GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS`` overrides built-in default."""

    if not include_domain_base:
        return ""
    env = (os.environ.get("GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS") or "").strip()
    return env if env else DEFAULT_CUSTOM_EXTRACTION_INSTRUCTIONS_EN


def build_merged_custom_extraction_instructions(
    *,
    custom_extraction_instructions: str | None,
    include_domain_extraction_base: bool,
    prepend_episode_source: bool,
    structural_extraction_guard: bool,
) -> str | None:
    """Order: domain base (env or default), caller ``custom_extraction_instructions``, structural guard."""

    parts: list[str] = []
    base = _domain_extraction_base_text(include_domain_base=include_domain_extraction_base).strip()
    if base:
        parts.append(base)
    if custom_extraction_instructions and str(custom_extraction_instructions).strip():
        parts.append(str(custom_extraction_instructions).strip())
    if prepend_episode_source and structural_extraction_guard:
        parts.append(STRUCTURAL_EXTRACTION_GUARD_EN.strip())
    return "\n\n".join(parts) if parts else None


def split_json_path(path: str | Path | None = None) -> Path:
    """JSON file path; ``None`` uses ``exp-g11-bio-1404.json``."""
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


# Keys from prepare ``metadata`` allowed on ``:Episodic`` (string or int as below).
EPISODE_METADATA_KEYS: frozenset[str] = frozenset(
    (
        "major",
        "grade",
        "subject",
        "chapter",
        "section",
        "publish_year",
        "chapter_id",
        "chapter_name",
        "section_id",
        "section_name",
        "json_row_index",
        "semantic_split_source_index",
    ),
)


def _meta_trimmed_str(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _meta_coerce_int(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        i = int(raw)
        if abs(raw - float(i)) < 1e-9:
            return i
        return None
    if isinstance(raw, str):
        xs = raw.strip()
        try:
            return int(xs, 10)
        except ValueError:
            return None
    return None


_PERSIAN_DIGIT_TABLE = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _int_to_persian_digits(n: int) -> str:
    return str(n).translate(_PERSIAN_DIGIT_TABLE)


def _load_exp_g11_bio_1404_metadata_catalog() -> dict[str, Any]:
    """Resolve ``metadata.exp_g11_bio_1404`` whether this file runs as ``-m graph.graph`` or ``graph/graph.py``."""

    try:
        from .metadata.exp_g11_bio_1404 import exp_g11_bio_1404_metadata
    except ImportError:
        try:
            from graph.metadata.exp_g11_bio_1404 import exp_g11_bio_1404_metadata
        except ImportError:
            from metadata.exp_g11_bio_1404 import exp_g11_bio_1404_metadata
    return exp_g11_bio_1404_metadata


def source_catalog_for_prepare_stem(stem: str) -> dict[str, Any] | None:
    """Return embedded chapter/section titles for known prepare JSON stems, else ``None``."""

    if stem == "exp-g11-bio-1404":
        return _load_exp_g11_bio_1404_metadata_catalog()
    return None


def episode_source_preface(metadata: dict[str, Any], catalog: dict[str, Any] | None) -> str | None:
    """Persian digits: ``منبع: فصل N (عنوان فصل) | گفتار M (عنوان گفتار)``; برای ``section`` ۰: ``… | مقدمه``."""

    rs = resolve_structural_source(metadata, catalog)
    if rs is None:
        return None
    pch = _int_to_persian_digits(rs.chapter_id)
    chap_part = (
        f"فصل {pch} ({rs.chapter_name})"
        if rs.chapter_name.strip()
        else f"فصل {pch}"
    )
    if rs.section_id == 0:
        suffix = "مقدمه"
    else:
        psec = _int_to_persian_digits(rs.section_id)
        suffix = (
            f"گفتار {psec} ({rs.section_name})"
            if rs.section_name.strip()
            else f"گفتار {psec}"
        )
    return f"منبع: {chap_part} | {suffix}"


def episode_body_with_source_preface(
    *,
    page_content: str,
    metadata: dict[str, Any],
    catalog: dict[str, Any] | None,
    prepend: bool = True,
) -> str:
    body = page_content.strip()
    if not prepend:
        return body
    preface = episode_source_preface(metadata, catalog)
    if preface:
        return f"{preface}\n\n{body}"
    return body


def episode_metadata_props(
    metadata: dict[str, Any],
    catalog: dict[str, Any] | None = None,
    *,
    json_row_index: int | None = None,
) -> dict[str, Any]:
    """Map prepare ``metadata`` (+ catalog titles + ingest row identity) onto ``:Episodic`` properties."""

    props: dict[str, Any] = {}
    mj = _meta_trimmed_str(metadata.get("major"))
    if mj is not None:
        props["major"] = mj
    sj = _meta_trimmed_str(metadata.get("subject"))
    if sj is not None:
        props["subject"] = sj
    for key in ("grade", "chapter", "section", "publish_year"):
        if key not in metadata:
            continue
        iv = _meta_coerce_int(metadata.get(key))
        if iv is not None:
            props[key] = iv

    rs = resolve_structural_source(metadata, catalog)
    if rs is not None:
        props["chapter_id"] = rs.chapter_id
        props["chapter_name"] = rs.chapter_name
        props["section_id"] = rs.section_id
        props["section_name"] = rs.section_name

    if json_row_index is not None:
        props["json_row_index"] = int(json_row_index)

    split_src = _meta_coerce_int(metadata.get("semantic_split_source_index"))
    if split_src is not None:
        props["semantic_split_source_index"] = split_src
    return props


async def apply_episode_metadata(
    driver: GraphDriver,
    episode_uuid: str,
    *,
    props: dict[str, Any],
) -> None:
    """SET allowed metadata keys on an existing ``:Episodic``."""

    allowed = {k: props[k] for k in props if k in EPISODE_METADATA_KEYS}
    if not allowed:
        return
    clauses = ", ".join(f"e.{k} = ${k}" for k in allowed)
    q = f"MATCH (e:Episodic {{uuid: $uuid}}) SET {clauses} RETURN e.uuid AS uuid"
    await driver.execute_query(q, uuid=episode_uuid, **allowed)


class _C:
    """ANSI؛ با ``NO_COLOR`` یا خروجی غیر-TTY خاموش."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GRAY = "\033[38;5;246m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[97m"


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stderr.isatty()


class IngestColorFormatter(logging.Formatter):
    """زمان کم‌رنگ، برچسب سطح، و تمایز نقش هر خط ingestion."""

    datefmt = "%H:%M:%S"

    _LEVEL_COL = {
        logging.DEBUG: _C.CYAN,
        logging.INFO: _C.GREEN,
        logging.WARNING: _C.YELLOW,
        logging.ERROR: _C.RED,
        logging.CRITICAL: _C.RED + _C.BOLD,
    }

    def __init__(self) -> None:
        super().__init__(fmt="%(message)s", datefmt=self.datefmt)
        self._color = _use_color()

    def _badge(self, record: logging.LogRecord) -> str:
        if not self._color:
            return f"{record.levelname:<9} |"
        col = self._LEVEL_COL.get(record.levelno, _C.WHITE)
        lv = record.levelname
        bar = _C.GRAY + _C.DIM + " |" + _C.RESET
        return f"{col}{_C.BOLD}{lv:<9}{_C.RESET}{bar}"

    _PREFIX_ACCENT = (
        ("ingest start ", _C.BLUE + _C.BOLD),
        ("resume: ", _C.YELLOW),
        ("resume skip ", _C.YELLOW + _C.DIM),
        ("add_episode json_row_index=", _C.CYAN + _C.BOLD),
        ("add_episode done ", _C.GREEN + _C.BOLD),
        ("ingest done ", _C.MAGENTA + _C.BOLD),
        ("limit reached ", _C.MAGENTA),
        ("build_indices_and_constraints ", _C.GRAY),
        ("resume off ", _C.YELLOW),
        ("+ graphiti:", _C.CYAN + _C.DIM),
        ("- graphiti:", _C.CYAN),
    )

    _KV_SPLIT = re.compile(
        r"(episode_name|json_row_index|group_id|skipped_resume|added"
        r"|path|stem|resume|limit|json_rows)=(\S+)",
    )

    def _shade_kv_plain(self, msg: str) -> str:
        if not self._color:
            return msg
        vk_for = {
            "episode_name": _C.CYAN,
            "group_id": _C.MAGENTA,
            "path": _C.BLUE,
            "stem": _C.BLUE,
            "json_row_index": _C.YELLOW,
        }

        fragments: list[str] = []
        prev = 0
        for m in self._KV_SPLIT.finditer(msg):
            if prev < m.start():
                fragments.append(_C.WHITE + msg[prev:m.start()] + _C.RESET)
            key, val = m.group(1), m.group(2)
            vk = vk_for.get(key, _C.GRAY)
            fragments.append(f"{_C.DIM}{key}={_C.RESET}{_C.BOLD}{vk}{val}{_C.RESET}")
            prev = m.end()

        fragments.append(_C.WHITE + msg[prev:] + _C.RESET)
        return "".join(fragments)

    def _shade_message(self, msg: str) -> str:
        if not self._color:
            return msg

        lead_len = len(msg) - len(msg.lstrip(" "))
        lead, rest = msg[:lead_len], msg[lead_len:]

        for pref, cc in self._PREFIX_ACCENT:
            if rest.startswith(pref):
                tail = rest[len(pref) :]
                return lead + cc + pref + _C.RESET + self._shade_kv_plain(tail)
        return self._shade_kv_plain(msg)

    def format(self, record: logging.LogRecord) -> str:
        ts_prefix = (
            f"{_C.GRAY}{self.formatTime(record, self.datefmt)}{_C.RESET} "
            if self._color
            else f"{self.formatTime(record, self.datefmt)} "
        )

        shaded = self._shade_message(record.getMessage())
        line = f"{ts_prefix}{self._badge(record)} {shaded}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        elif record.exc_text:
            line += "\n" + record.exc_text
        return line


def configure_ingest_logging(*, level: int = logging.INFO, quiet_other_loggers: bool = True) -> None:
    """هندلر رنگی برای ``ingestion.graph.graph`` و (در صورت نیاز) Graphiti trace؛ ریشه را خالی می‌گذارد."""

    def attach(name: str) -> None:
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.setLevel(level)
        lg.propagate = False
        h = logging.StreamHandler(sys.stderr)
        h.setLevel(level)
        h.setFormatter(IngestColorFormatter())
        lg.addHandler(h)

    attach("ingestion.graph.graph")
    attach("ingestion.graphiti.trace")
    attach("config.graphiti")

    if quiet_other_loggers:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)


@dataclass(frozen=True)
class IngestStats:
    """Result of ``ingest_split_json``."""

    added: int
    skipped_already_in_graph: int


async def _existing_doc_indices(*, driver: GraphDriver, stem: str, group_id: str) -> frozenset[int]:
    """Row indices ``i`` for which ``{stem}-{i:05d}`` already exists as an Episodic name."""
    prefix = f"{stem}-"
    records, _, _ = await driver.execute_query(
        """
        MATCH (n:Episodic)
        WHERE n.group_id = $group_id AND n.name STARTS WITH $prefix
        RETURN n.name AS name
        """,
        group_id=group_id,
        prefix=prefix,
    )
    indices: set[int] = set()
    pl = len(prefix)
    for row in records:
        name = row.get("name")
        if not isinstance(name, str) or len(name) < pl + 5:
            continue
        if not name.startswith(prefix):
            continue
        tail = name[pl:]
        if len(tail) == 5 and tail.isdigit():
            indices.add(int(tail))
    return frozenset(indices)


async def ingest_split_json(
    graphiti: Graphiti,
    path: str | Path | None = None,
    *,
    # FalkorGraphiti maps group_id → Falkor graph name when != driver.database; keep aligned with FALKOR_DATABASE.
    group_id: str = FALKOR_DATABASE,
    setup_db: bool = True,
    limit: int | None = None,
    resume: bool = True,
    persist_metadata: bool = True,
    custom_extraction_instructions: str | None = None,
    include_domain_extraction_base: bool = True,
    structural_extraction_guard: bool = True,
    prepend_episode_source: bool = True,
    episode_source_catalog: dict[str, Any] | None = None,
    model_textbook_structure: bool = True,
    add_episode_label: bool = False,
    section_to_episode_rel_type: str = "SECTION_HAS_EPISODE",
) -> IngestStats:
    """One episode per non-empty ``page_content``; skips rows already stored (same ``name``, same ``group_id``).

    Episode names follow ``"{stem}-{row_index:05d}"`` so rerun after interruption continues safely.

    When ``persist_metadata`` is true, ``metadata`` fields (``major``, ``grade``, ``subject``, …),
    structural chapter/section titles, ``json_row_index`` (0-based JSON row, for accurate ``ORDER BY``
    within a Section — **not** lexicographic ``name`` order), and optional ``semantic_split_source_index``
    from the prepare row are SET on ``:Episodic`` after each successful ``add_episode``.

    When ``prepend_episode_source`` is true (default), each ``episode_body`` begins with ``منبع:`` —
    ``فصل n (نام فصل) | گفتار m (نام گفتار)`` with Persian numerals (section ``0`` uses ``| مقدمه``).
    Titles resolve from ``episode_source_catalog`` / known stems.

    When ``model_textbook_structure`` is true and a textbook catalog exists, ingestion MERGEs
    ``Book`` / ``Chapter`` / ``Section`` nodes plus ``HAS_CHAPTER`` / ``HAS_SECTION``, links each
    new ``Episodic`` from ``Section`` via ``SECTION_HAS_EPISODE`` by default (``HAS_EPISODE`` Saga-type
    rel name is avoided unless ``section_to_episode_rel_type`` is set to ``HAS_EPISODE``), and optionally
    labels ``Episodic`` additionally as ``Episode`` when ``add_episode_label`` is true.

    By default, ``custom_extraction_instructions`` passed to Graphiti is ``None`` (library built-in
    extraction). Set ``include_domain_extraction_base=True`` to layer env
    ``GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS`` or ``DEFAULT_CUSTOM_EXTRACTION_INSTRUCTIONS_EN``, and/or
    pass ``custom_extraction_instructions`` for an extra middle layer. When ``prepend_episode_source``
    and ``structural_extraction_guard`` are both true, structural-scaffolding instructions are appended
    (the «منبع:» header plus bare figure/image/chart callouts such as «شکل ۱» / «تصویر ۱» / «نمودار ۱»).

    Set ``INGEST_TRACE_TIMING`` to a truthy value (``1``, ``true``, ``yes``, ``y``, ``on``) to log wall times
    for ``build_indices_and_constraints``, the resume Cypher query, each ``add_episode`` vs
    ``apply_episode_metadata`` vs textbook-structure writes, and summed averages at the end.
    Set ``INGEST_GRAPHITI_TRACE`` to log nested Graphiti spans (each ``llm.generate`` with ``prompt.name``);
    ``INGEST_GRAPHITI_TRACE_VERBOSE=1`` dumps all span attributes.
    """
    path = split_json_path(path)
    rows = load_docs(path)
    stem = path.stem

    structure_catalog = episode_source_catalog
    if structure_catalog is None and (prepend_episode_source or model_textbook_structure):
        structure_catalog = source_catalog_for_prepare_stem(stem)

    merged_custom_extraction = build_merged_custom_extraction_instructions(
        custom_extraction_instructions=custom_extraction_instructions,
        include_domain_extraction_base=include_domain_extraction_base,
        prepend_episode_source=prepend_episode_source,
        structural_extraction_guard=structural_extraction_guard,
    )
    logger.info(
        "ingest start path=%s stem=%s group_id=%s resume=%s limit=%s json_rows=%s",
        path,
        stem,
        group_id,
        resume,
        limit,
        len(rows),
    )

    _trace = _ingest_trace_timing_enabled()
    if _trace:
        logger.info(
            "ingest trace timing enabled (INGEST_TRACE_TIMING=%r)",
            (os.environ.get("INGEST_TRACE_TIMING") or "").strip(),
        )
    sum_add_episode_s = 0.0
    sum_metadata_s = 0.0
    sum_struct_s = 0.0
    n_timed_episodes = 0

    if setup_db:
        logger.info("build_indices_and_constraints ...")
        t_bi = time.perf_counter()
        await graphiti.build_indices_and_constraints()
        if _trace:
            logger.info("timing build_indices_and_constraints %.3fs", time.perf_counter() - t_bi)

    if model_textbook_structure and isinstance(structure_catalog, dict) and structure_catalog.get("chapters"):
        logger.info(
            "textbook structure MERGE (Book → Chapter → Section) from catalog textbook_id=%r group_id=%r",
            stem,
            group_id,
        )
        t_sk = time.perf_counter()
        await ensure_textbook_structure_skeleton(
            graphiti.driver,
            group_id=group_id,
            textbook_id=stem,
            catalog=structure_catalog,
        )
        if _trace:
            logger.info(
                "timing ensure_textbook_structure_skeleton %.3fs",
                time.perf_counter() - t_sk,
            )

    existing: frozenset[int] = frozenset()
    if resume:
        t_ex = time.perf_counter()
        existing = await _existing_doc_indices(
            driver=graphiti.driver,
            stem=stem,
            group_id=group_id,
        )
        if _trace:
            logger.info(
                "timing resume_existing_episode_query %.3fs (rows=%s)",
                time.perf_counter() - t_ex,
                len(existing),
            )
        if existing:
            logger.info(
                "resume: %s episode(s) already in graph for name prefix %r (row indices %s..%s)",
                len(existing),
                f"{stem}-",
                min(existing),
                max(existing),
            )
        else:
            logger.info("resume: no matching episodes in graph yet for prefix %r", f"{stem}-")
    else:
        logger.info("resume off - every non-empty row will call add_episode")

    added = 0
    skipped = 0
    for i, row in enumerate(rows):
        if limit is not None and added >= limit:
            logger.info("limit reached (%s new episode(s) this run); stopping", limit)
            break
        text = row.get("page_content")
        if not isinstance(text, str) or not text.strip():
            logger.debug("skip json_row_index=%s (empty page_content)", i)
            continue

        ep_name = f"{stem}-{i:05d}"
        if resume and i in existing:
            skipped += 1
            logger.info(
                "resume skip json_row_index=%s episode_name=%s (already in graph)",
                i,
                ep_name,
            )
            continue

        logger.info(
            "add_episode json_row_index=%s episode_name=%s group_id=%s ...",
            i,
            ep_name,
            group_id,
        )
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        src_desc = f"{stem} #{i} ({meta.get('filename', '?')})"
        episode_body = episode_body_with_source_preface(
            page_content=text,
            metadata=meta,
            catalog=structure_catalog,
            prepend=prepend_episode_source,
        )
        t_ae = time.perf_counter()
        result = await _add_episode_with_retry(
            graphiti,
            name=ep_name,
            episode_body=episode_body,
            source_description=src_desc,
            reference_time=_ref_time(meta),
            source=EpisodeType.text,
            group_id=group_id,
            custom_extraction_instructions=merged_custom_extraction,
        )
        logger.info(
            "add_episode extracted episode_name=%s uuid=%s entities=%s entity_edges=%s episodic_edges=%s",
            ep_name,
            result.episode.uuid,
            len(result.nodes),
            len(result.edges),
            len(result.episodic_edges),
        )
        dt_add = time.perf_counter() - t_ae
        dt_meta = 0.0
        dt_struct = 0.0

        if persist_metadata:
            t_md = time.perf_counter()
            await apply_episode_metadata(
                graphiti.driver,
                result.episode.uuid,
                props=episode_metadata_props(meta, structure_catalog, json_row_index=i),
            )
            dt_meta = time.perf_counter() - t_md
        if model_textbook_structure:
            t_st = time.perf_counter()
            if add_episode_label:
                await label_episodic_as_episode(
                    graphiti.driver,
                    group_id=group_id,
                    episodic_uuid=result.episode.uuid,
                )
            rs = resolve_structural_source(meta, structure_catalog)
            if rs is not None:
                await link_section_has_episode(
                    graphiti.driver,
                    group_id=group_id,
                    textbook_id=stem,
                    chapter_id=rs.chapter_id,
                    section_id=rs.section_id,
                    episodic_uuid=result.episode.uuid,
                    relationship_type=section_to_episode_rel_type,
                )
            dt_struct = time.perf_counter() - t_st
        if _trace:
            sum_add_episode_s += dt_add
            sum_metadata_s += dt_meta
            sum_struct_s += dt_struct
            n_timed_episodes += 1
            logger.info(
                "timing episode=%s add_episode=%.3fs apply_metadata=%.3fs textbook_structure=%.3fs",
                ep_name,
                dt_add,
                dt_meta,
                dt_struct,
            )
        added += 1
        logger.info("add_episode done episode_name=%s", ep_name)

    if _trace and n_timed_episodes:
        n = n_timed_episodes
        logger.info(
            "timing totals (%s episode(s)): add_episode sum=%.3fs avg=%.3fs | "
            "apply_metadata sum=%.3fs avg=%.3fs | textbook_structure sum=%.3fs avg=%.3fs",
            n,
            sum_add_episode_s,
            sum_add_episode_s / n,
            sum_metadata_s,
            sum_metadata_s / n,
            sum_struct_s,
            sum_struct_s / n,
        )

    logger.info(
        "ingest done added=%s skipped_resume=%s",
        added,
        skipped,
    )
    return IngestStats(added=added, skipped_already_in_graph=skipped)


async def main() -> None:
    configure_ingest_logging(level=logging.INFO)

    from config.graphiti import create_graphiti

    g = create_graphiti()
    try:
        stats = await ingest_split_json(g)
        suffix = ""
        if stats.skipped_already_in_graph:
            suffix = f" ({stats.skipped_already_in_graph} already in graph)"

        plain = f"Imported {stats.added} new episodes{suffix}"
        if not _use_color():
            print(plain)
            return

        line = (
            f"{_C.BOLD}{_C.GREEN}Imported{_C.RESET}"
            f" {_C.BOLD}{_C.CYAN}{stats.added}{_C.RESET} new episodes{_C.WHITE}{suffix}{_C.RESET}"
        )
        print(line)
    finally:
        await g.close()


if __name__ == "__main__":
    asyncio.run(main())
