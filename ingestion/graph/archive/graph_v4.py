"""Load split-doc JSON and push episodes to Graphiti.

Curriculum facets (``cv_*``) are written on ``Episodic`` nodes after each ``add_episode`` so you
can filter in Cypher (``MATCH (e:Episodic) WHERE e.cv_subject = $subject ...``). Graphiti's
``episode_fulltext_search`` path does not apply ``SearchFilters.property_filters``, so after
``search_`` use ``filter_search_results_by_episode_facets`` (or ``curriculum_episode_where`` in
custom Cypher) to restrict episodes and derived edges/nodes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.driver.driver import GraphDriver
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EntityNode, EpisodeType
from graphiti_core.search.search_config import SearchResults

from ingestion.config.falkordb import FALKOR_DATABASE

# ثابت تا با اجرای مستقیم‌ی فایل (__main__) هم همان هندلر رنگی گیرد.
logger = logging.getLogger("ingestion.graph.graph")

DEFAULT_SPLIT_JSON = (
    Path(__file__).resolve().parent.parent
    / "data/prepare/exp-g11-bio/exp-g11-bio-1404.json"
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


# --- Episodic curriculum facets (persisted for Cypher filtering) ---

CV_MAJOR = "cv_major"
CV_GRADE = "cv_grade"
CV_SUBJECT = "cv_subject"
CV_CHAPTER = "cv_chapter"
CV_SECTION = "cv_section"
CV_PUBLISH_YEAR = "cv_publish_year"

EPISODE_CV_PROPERTY_NAMES: tuple[str, ...] = (
    CV_MAJOR,
    CV_GRADE,
    CV_SUBJECT,
    CV_CHAPTER,
    CV_SECTION,
    CV_PUBLISH_YEAR,
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


def episodic_cv_props_from_prepare_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Map ``metadata`` rows from prepared JSON onto ``Episodic`` facet properties."""

    cv: dict[str, Any] = {}
    mj = _meta_trimmed_str(metadata.get("major"))
    if mj is not None:
        cv[CV_MAJOR] = mj
    sj = _meta_trimmed_str(metadata.get("subject"))
    if sj is not None:
        cv[CV_SUBJECT] = sj
    for meta_key, prop in (
        ("grade", CV_GRADE),
        ("chapter", CV_CHAPTER),
        ("section", CV_SECTION),
        ("publish_year", CV_PUBLISH_YEAR),
    ):
        if meta_key not in metadata:
            continue
        iv = _meta_coerce_int(metadata.get(meta_key))
        if iv is None:
            continue
        cv[prop] = iv
    return cv


async def apply_curriculum_facets_to_episode(
    driver: GraphDriver,
    episode_uuid: str,
    *,
    facets: dict[str, Any],
) -> None:
    """SET curriculum facet keys on ``:Episodic`` (must already exist).

    Keys must be listed in ``EPISODE_CV_PROPERTY_NAMES`` — extra keys are ignored.
    """
    allowed = {k: facets[k] for k in facets if k in EPISODE_CV_PROPERTY_NAMES}
    if not allowed:
        return
    clauses = ", ".join(f"e.{k} = ${k}" for k in allowed)
    q = (
        "MATCH (e:Episodic {uuid: $uuid}) SET "
        + clauses
        + " RETURN e.uuid AS uuid"
    )
    await driver.execute_query(q, uuid=episode_uuid, **allowed)


def curriculum_episode_where(
    *,
    alias: str = "e",
    major: str | None = None,
    grade: int | None = None,
    subject: str | None = None,
    chapter: int | None = None,
    section: int | None = None,
    publish_year: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """Build a conjunction of comparisons and bind parameters.

    Prefix ``cv_fil_`` on parameters avoids clashing with other query placeholders.
    """
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if major is not None:
        clauses.append(f"{alias}.{CV_MAJOR} = $cv_fil_major")
        params["cv_fil_major"] = major
    if grade is not None:
        clauses.append(f"{alias}.{CV_GRADE} = $cv_fil_grade")
        params["cv_fil_grade"] = grade
    if subject is not None:
        clauses.append(f"{alias}.{CV_SUBJECT} = $cv_fil_subject")
        params["cv_fil_subject"] = subject
    if chapter is not None:
        clauses.append(f"{alias}.{CV_CHAPTER} = $cv_fil_chapter")
        params["cv_fil_chapter"] = chapter
    if section is not None:
        clauses.append(f"{alias}.{CV_SECTION} = $cv_fil_section")
        params["cv_fil_section"] = section
    if publish_year is not None:
        clauses.append(f"{alias}.{CV_PUBLISH_YEAR} = $cv_fil_publish_year")
        params["cv_fil_publish_year"] = publish_year
    return (" AND ".join(clauses), params)


def _score_at(scores: list[float], i: int) -> float:
    if i < len(scores):
        return scores[i]
    return 0.0


async def filter_search_results_by_episode_facets(
    driver: GraphDriver,
    results: SearchResults,
    *,
    group_id: str | None = None,
    major: str | None = None,
    grade: int | None = None,
    subject: str | None = None,
    chapter: int | None = None,
    section: int | None = None,
    publish_year: int | None = None,
) -> SearchResults:
    """Drop edges/episodes/nodes not grounded in episodes matching curriculum facets.

    Graphiti does not apply ``SearchFilters.property_filters`` to search. After
    ``Graphiti.search_``, call this with the same ``cv_*`` constraints you persist
    on ``:Episodic`` (see ``apply_curriculum_facets_to_episode``).

    Episodes are kept iff their uuid matches the facet query. Edges are kept if at
    least one uuid in ``edge.episodes`` matches. Nodes are the endpoints of kept
    edges (order follows the original node list).
    """

    where_cv, params_cv = curriculum_episode_where(
        alias="e",
        major=major,
        grade=grade,
        subject=subject,
        chapter=chapter,
        section=section,
        publish_year=publish_year,
    )
    if not where_cv:
        return results

    candidate: set[str] = {ep.uuid for ep in results.episodes}
    for edge in results.edges:
        candidate.update(edge.episodes)

    if not candidate:
        return SearchResults()

    group_clause = ""
    q_params: dict[str, Any] = {
        "candidate_uuids": list(candidate),
        **params_cv,
    }
    if group_id is not None:
        group_clause = " AND e.group_id = $group_id"
        q_params["group_id"] = group_id

    q = (
        "MATCH (e:Episodic)\nWHERE e.uuid IN $candidate_uuids"
        + group_clause
        + " AND "
        + where_cv
        + "\nRETURN e.uuid AS uuid"
    )
    records, _, _ = await driver.execute_query(q, **q_params)
    allowed = {str(row["uuid"]) for row in records if row.get("uuid")}

    if not allowed:
        return SearchResults()

    ep_keep = [ep for ep in results.episodes if ep.uuid in allowed]
    ep_scores = [
        _score_at(results.episode_reranker_scores, i)
        for i, ep in enumerate(results.episodes)
        if ep.uuid in allowed
    ]

    edge_keep: list[EntityEdge] = []
    edge_scores: list[float] = []
    for i, edge in enumerate(results.edges):
        eps = edge.episodes
        if not eps or allowed.isdisjoint(eps):
            continue
        edge_keep.append(edge)
        edge_scores.append(_score_at(results.edge_reranker_scores, i))

    endpoint: set[str] = set()
    for edge in edge_keep:
        endpoint.add(edge.source_node_uuid)
        endpoint.add(edge.target_node_uuid)

    node_keep: list[EntityNode] = []
    node_scores: list[float] = []
    for i, node in enumerate(results.nodes):
        if node.uuid in endpoint:
            node_keep.append(node)
            node_scores.append(_score_at(results.node_reranker_scores, i))

    return SearchResults(
        edges=edge_keep,
        edge_reranker_scores=edge_scores,
        nodes=node_keep,
        node_reranker_scores=node_scores,
        episodes=ep_keep,
        episode_reranker_scores=ep_scores,
        communities=results.communities,
        community_reranker_scores=results.community_reranker_scores,
    )


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
    group_id: str = "FALKOR_DATABASE",
    setup_db: bool = True,
    limit: int | None = None,
    resume: bool = True,
    persist_curriculum_facets: bool = True,
) -> IngestStats:
    """One episode per non-empty ``page_content``; skips rows already stored (same ``name``, same ``group_id``).

    Episode names follow ``"{stem}-{row_index:05d}"`` so rerun after interruption continues safely.

    After each successful ``add_episode``, optional ``cv_*`` fields are SET on ``:Episodic`` when
    ``persist_curriculum_facets`` is true (see ``curriculum_episode_where``).
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

    if setup_db:
        logger.info("build_indices_and_constraints ...")
        await graphiti.build_indices_and_constraints()

    existing: frozenset[int] = frozenset()
    if resume:
        existing = await _existing_doc_indices(
            driver=graphiti.driver,
            stem=stem,
            group_id=group_id,
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
        result = await graphiti.add_episode(
            name=ep_name,
            episode_body=text.strip(),
            source_description=src_desc,
            reference_time=_ref_time(meta),
            source=EpisodeType.text,
            group_id=group_id,
        )
        if persist_curriculum_facets:
            facets = episodic_cv_props_from_prepare_metadata(meta)
            await apply_curriculum_facets_to_episode(
                graphiti.driver,
                result.episode.uuid,
                facets=facets,
            )
        added += 1
        logger.info("add_episode done episode_name=%s", ep_name)

    logger.info(
        "ingest done added=%s skipped_resume=%s",
        added,
        skipped,
    )
    return IngestStats(added=added, skipped_already_in_graph=skipped)


async def main() -> None:
    configure_ingest_logging(level=logging.INFO)

    from ingestion.config.graphiti import create_graphiti

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
