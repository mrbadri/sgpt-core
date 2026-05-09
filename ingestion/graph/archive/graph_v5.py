"""Load split-doc JSON and push episodes to Graphiti.
Version Before add  metedata and all feat work good

Optional fields from each row's ``metadata`` (``major``, ``grade``, ``subject``, …) are written
on ``:Episodic`` after ``add_episode`` so you can filter in Cypher, e.g.
``WHERE e.subject = $subject AND e.grade = $grade``.
"""

from __future__ import annotations

import asyncio
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
from graphiti_core.nodes import EpisodeType

from config.falkordb import FALKOR_DATABASE

# ثابت تا با اجرای مستقیم‌ی فایل (__main__) هم همان هندلر رنگی گیرد.
logger = logging.getLogger("ingestion.graph.graph")


def _ingest_trace_timing_enabled() -> bool:
    v = (os.environ.get("INGEST_TRACE_TIMING") or "").strip().lower()
    return v in ("1", "true", "yes")

DEFAULT_SPLIT_JSON = (
    Path(__file__).resolve().parent.parent
    / "data/normalize/exp-g11-bio/exp-g11-bio-1404.json"
)

# Shown to Graphiti entity/edge extraction when ``GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS`` is unset.
DEFAULT_CUSTOM_EXTRACTION_INSTRUCTIONS_EN = (
    "You are reading instructional text from a Persian (Farsi) high-school biology textbook. "
    "Extract the underlying concepts and important substantive terms people might see referenced "
    "again elsewhere (other sections, exams, etc.).\n\n"
    "PERSIAN SPELLING (STRICT): When you name an entity, reuse the exact phrase as it appears in "
    "the episode, character-for-character, including the zero-width non-joiner (ZWNJ, Unicode U+200C) "
    "where the source has it. Do not 'normalize', join, or strip ZWNJ to 'fix' typography.\n\n"
    "Persian often inserts ZWNJ before suffixes such as plural «های» / «ها» or ezafe «ی» so that "
    "affixes stay graphically separate from the stem. A common model failure is gluing stem + "
    "suffix with no ZWNJ.\n"
    "BAD output: «یاختههای» (wrong—suffix stuck to the stem).\n"
    "GOOD output: «یاخته‌های» when the passage uses the half-space before «های»—copy that form.\n\n"
    "If the phrase in the text already lacks ZWNJ, still do not invent merges that blur two words; "
    "prefer quoting the minimal exact substring from the text as the entity name."
)


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
    ("major", "grade", "subject", "chapter", "section", "publish_year"),
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


def episode_metadata_props(metadata: dict[str, Any]) -> dict[str, Any]:
    """Map prepare ``metadata`` to properties stored on ``:Episodic``."""

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

        for pref, cc in self._PREFIX_ACCENT:
            if msg.startswith(pref):
                tail = msg[len(pref) :]
                return cc + pref + _C.RESET + self._shade_kv_plain(tail)
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
    """هندلر رنگی فقط برای ``ingestion.graph.graph``؛ ریشه را خالی می‌گذارد."""
    ingest_l = logging.getLogger("ingestion.graph.graph")

    ingest_l.handlers.clear()
    ingest_l.setLevel(level)
    ingest_l.propagate = False

    h = logging.StreamHandler(sys.stderr)
    h.setLevel(level)
    h.setFormatter(IngestColorFormatter())
    ingest_l.addHandler(h)

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
) -> IngestStats:
    """One episode per non-empty ``page_content``; skips rows already stored (same ``name``, same ``group_id``).

    Episode names follow ``"{stem}-{row_index:05d}"`` so rerun after interruption continues safely.

    When ``persist_metadata`` is true, ``metadata`` fields (``major``, ``grade``, ``subject``, …)
    are SET on ``:Episodic`` after each successful ``add_episode``.

    ``custom_extraction_instructions`` is forwarded to Graphiti ``add_episode`` (entity + edge extraction
    prompts); use it to bias terminology, domain (e.g. biology), or language.

    Set ``INGEST_TRACE_TIMING=1`` to log wall times for ``build_indices_and_constraints``, the resume
    Cypher query, each ``add_episode`` vs ``apply_episode_metadata``, and summed averages at the end.
    """
    path = split_json_path(path)
    rows = load_docs(path)
    stem = path.stem

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
    sum_add_episode_s = 0.0
    sum_metadata_s = 0.0
    n_timed_episodes = 0

    if setup_db:
        logger.info("build_indices_and_constraints ...")
        t_bi = time.perf_counter()
        await graphiti.build_indices_and_constraints()
        if _trace:
            logger.info("timing build_indices_and_constraints %.3fs", time.perf_counter() - t_bi)

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
        t_ae = time.perf_counter()
        result = await graphiti.add_episode(
            name=ep_name,
            episode_body=text.strip(),
            source_description=src_desc,
            reference_time=_ref_time(meta),
            source=EpisodeType.text,
            group_id=group_id,
            custom_extraction_instructions=custom_extraction_instructions,
        )
        dt_add = time.perf_counter() - t_ae
        dt_meta = 0.0
        if persist_metadata:
            t_md = time.perf_counter()
            await apply_episode_metadata(
                graphiti.driver,
                result.episode.uuid,
                props=episode_metadata_props(meta),
            )
            dt_meta = time.perf_counter() - t_md
        if _trace:
            sum_add_episode_s += dt_add
            sum_metadata_s += dt_meta
            n_timed_episodes += 1
            logger.info(
                "timing episode=%s add_episode=%.3fs apply_metadata=%.3fs",
                ep_name,
                dt_add,
                dt_meta,
            )
        added += 1
        logger.info("add_episode done episode_name=%s", ep_name)

    if _trace and n_timed_episodes:
        logger.info(
            "timing totals (%s episode(s)): add_episode sum=%.3fs avg=%.3fs | "
            "apply_metadata sum=%.3fs avg=%.3fs",
            n_timed_episodes,
            sum_add_episode_s,
            sum_add_episode_s / n_timed_episodes,
            sum_metadata_s,
            sum_metadata_s / n_timed_episodes,
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

    extra = (os.environ.get("GRAPHITI_CUSTOM_EXTRACTION_INSTRUCTIONS") or "").strip()
    if not extra:
        extra = DEFAULT_CUSTOM_EXTRACTION_INSTRUCTIONS_EN
    g = create_graphiti()
    try:
        stats = await ingest_split_json(
            g,
            # custom_extraction_instructions=extra or None,
        )
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
