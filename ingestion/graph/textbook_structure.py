"""Textbook scaffolding in the Falkor/graph store alongside Graphiti.

Graphiti persists narrative units as ``:Episodic`` nodes; this module adds Book / Chapter /
Section scaffolding. ``Section`` connects to episodes with ``SECTION_HAS_EPISODE`` by default
(separate from Graphiti Saga ``HAS_EPISODE``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from graphiti_core.driver.driver import GraphDriver

# Default edge from Section → Episodic (distinct from Graphiti Saga `HAS_EPISODE` to avoid UI/query confusion).
STRUCTURAL_SECTION_EPISODE_REL = "SECTION_HAS_EPISODE"
LEGACY_SECTION_EPISODE_REL = "HAS_EPISODE"


@dataclass(frozen=True)
class ResolvedStructuralSource:
    """Chapter/section identifiers and display names from prepare metadata + textbook catalog."""

    chapter_id: int
    chapter_name: str
    section_id: int
    section_name: str


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


def book_display_name_from_catalog(catalog: dict[str, Any], textbook_id: str) -> str:
    """Use ``catalog["title"]`` when set; otherwise a readable form of ``textbook_id``."""

    title = _meta_trimmed_str(catalog.get("title"))
    if title:
        return title
    return textbook_id.replace("-", " ").strip()


def resolve_structural_source(metadata: dict[str, Any], catalog: dict[str, Any] | None) -> ResolvedStructuralSource | None:
    ch = _meta_coerce_int(metadata.get("chapter"))
    sec = _meta_coerce_int(metadata.get("section"))
    if ch is None or sec is None:
        return None

    ch_name = ""
    sec_name = ""
    if catalog:
        chapters = catalog.get("chapters")
        if isinstance(chapters, dict):
            ch_info = chapters.get(str(ch))
            if isinstance(ch_info, dict):
                ch_name = _meta_trimmed_str(ch_info.get("name")) or ""
                sections = ch_info.get("sections")
                if isinstance(sections, dict):
                    sr = sections.get(str(sec))
                    if isinstance(sr, dict):
                        sec_name = _meta_trimmed_str(sr.get("name")) or ""

    return ResolvedStructuralSource(
        chapter_id=ch,
        chapter_name=ch_name,
        section_id=sec,
        section_name=sec_name,
    )


async def ensure_textbook_structure_skeleton(
    driver: GraphDriver,
    *,
    group_id: str,
    textbook_id: str,
    catalog: dict[str, Any],
) -> None:
    """MERGE Book, Chapter(s), Section(s) plus HAS_CHAPTER / HAS_SECTION."""

    chapters = catalog.get("chapters")
    if not isinstance(chapters, dict):
        return

    book_name = book_display_name_from_catalog(catalog, textbook_id)
    await driver.execute_query(
        """
        MERGE (b:Book {group_id: $group_id, textbook_id: $textbook_id})
        ON CREATE SET b.name = $book_name
        """,
        group_id=group_id,
        textbook_id=textbook_id,
        book_name=book_name,
    )

    for ck, ch_payload in chapters.items():
        cid = _meta_coerce_int(ck)
        if cid is None or not isinstance(ch_payload, dict):
            continue
        cname = _meta_trimmed_str(ch_payload.get("name")) or ""
        await driver.execute_query(
            """
            MERGE (c:Chapter {group_id: $group_id, textbook_id: $textbook_id, chapter_id: $chapter_id})
            ON CREATE SET c.name = $chapter_name
            WITH c
            MERGE (b:Book {group_id: $group_id, textbook_id: $textbook_id})
            MERGE (b)-[:HAS_CHAPTER]->(c)
            """,
            group_id=group_id,
            textbook_id=textbook_id,
            chapter_id=cid,
            chapter_name=cname,
        )

        secs = ch_payload.get("sections")
        if not isinstance(secs, dict):
            continue
        for sk, sec_payload in secs.items():
            sid = _meta_coerce_int(sk)
            if sid is None or not isinstance(sec_payload, dict):
                continue
            sname = _meta_trimmed_str(sec_payload.get("name")) or ""
            await driver.execute_query(
                """
                MERGE (s:Section {group_id: $group_id, textbook_id: $textbook_id, chapter_id: $chapter_id, section_id: $section_id})
                ON CREATE SET s.name = $section_name
                WITH s
                MERGE (c:Chapter {group_id: $group_id, textbook_id: $textbook_id, chapter_id: $chapter_id})
                MERGE (c)-[:HAS_SECTION]->(s)
                """,
                group_id=group_id,
                textbook_id=textbook_id,
                chapter_id=cid,
                section_id=sid,
                section_name=sname,
            )


async def label_episodic_as_episode(
    driver: GraphDriver,
    *,
    group_id: str,
    episodic_uuid: str,
) -> None:
    """Add ``Episode`` secondary label alongside Graphiti's ``Episodic``."""

    await driver.execute_query(
        """
        MATCH (e:Episodic {uuid: $uuid})
        SET e:Episode
        """,
        uuid=episodic_uuid,
    )


async def link_section_has_episode(
    driver: GraphDriver,
    *,
    group_id: str,
    textbook_id: str,
    chapter_id: int,
    section_id: int,
    episodic_uuid: str,
    relationship_type: str = STRUCTURAL_SECTION_EPISODE_REL,
) -> None:
    """``Section`` → ``Episodic`` structural link (default rel ``SECTION_HAS_EPISODE``, not Saga ``HAS_EPISODE``)."""

    if relationship_type not in (STRUCTURAL_SECTION_EPISODE_REL, LEGACY_SECTION_EPISODE_REL):
        raise ValueError(
            f"relationship_type must be {STRUCTURAL_SECTION_EPISODE_REL!r} or {LEGACY_SECTION_EPISODE_REL!r}, "
            f"got {relationship_type!r}",
        )

    await driver.execute_query(
        f"""
        MATCH (sec:Section {{group_id: $group_id, textbook_id: $textbook_id, chapter_id: $chapter_id, section_id: $section_id}})
        MATCH (ep:Episodic {{uuid: $uuid}})
        MERGE (sec)-[:{relationship_type}]->(ep)
        """,
        group_id=group_id,
        textbook_id=textbook_id,
        chapter_id=chapter_id,
        section_id=section_id,
        uuid=episodic_uuid,
    )
