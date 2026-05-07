"""High-level async search over Graphiti (edges + episodes)."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from graphiti_core import Graphiti

from app.config.graphiti import get_graphiti_settings
from app.knowledge_graph.client import create_graphiti
from app.knowledge_graph.search_config import (
    DEFAULT_SEARCH_LIMIT,
    RESULT_LIMIT_PER_CATEGORY,
    search_config_cross_encoder_no_bfs,
    search_config_rrf_no_bfs,
)

# Upper bound for concurrent searches per batch (avoid runaway tool calls).
MAX_BATCH_QUERIES = 20


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _unique(items: list[Any], key_fn) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        k = _normalize(key_fn(item))
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


@dataclass
class ConceptSearchResult:
    edges: list[Any]
    episodes: list[Any]


async def search_concepts(
    query: str,
    *,
    group_ids: list[str] | None = None,
    limit: int | None = None,
    graphiti: Graphiti | None = None,
    close_client: bool | None = None,
) -> ConceptSearchResult:
    """Run conceptual search; owns client lifecycle when ``graphiti`` is omitted."""

    settings = get_graphiti_settings()
    effective_limit = (
        limit if limit is not None else settings.graphiti_search_limit or DEFAULT_SEARCH_LIMIT
    )

    own = graphiti is None
    # FalkorDB sync-connects in driver __init__; avoid blocking the LangGraph / ASGI event loop.
    if graphiti is not None:
        g = graphiti
    else:
        g = await asyncio.to_thread(create_graphiti)
    should_close = close_client if close_client is not None else own

    try:
        if settings.graphiti_search_preset == "rrf":
            cfg = search_config_rrf_no_bfs(limit=effective_limit)
        else:
            cfg = search_config_cross_encoder_no_bfs(limit=effective_limit)
        results = await g.search_(query, config=cfg, group_ids=group_ids)
        edges = _unique(results.edges, lambda e: e.fact)[:RESULT_LIMIT_PER_CATEGORY]
        episodes = _unique(results.episodes, lambda ep: ep.content)[:RESULT_LIMIT_PER_CATEGORY]
        return ConceptSearchResult(edges=edges, episodes=episodes)
    finally:
        if should_close:
            await g.close()


def _nonempty_queries(queries: Sequence[str]) -> list[str]:
    """Strip and drop empty strings; preserve order of remaining items."""

    out: list[str] = []
    for q in queries:
        t = _normalize(q) if q else ""
        if t:
            out.append(t)
    return out


def nonempty_batch_queries(queries: Sequence[str]) -> list[str]:
    """Strip and drop empty strings; same filter as :func:`search_concepts_batch`."""

    return _nonempty_queries(queries)


async def search_concepts_batch(
    queries: Sequence[str],
    *,
    group_ids: list[str] | None = None,
    limit: int | None = None,
) -> list[ConceptSearchResult]:
    """Run ``search_concepts`` for each query concurrently (independent clients per query).

    Empty strings are skipped. Raises ``ValueError`` if no non-empty queries remain or if
    more than :data:`MAX_BATCH_QUERIES` queries are given.
    """

    normalized = nonempty_batch_queries(queries)
    if not normalized:
        raise ValueError("At least one non-empty query is required.")
    if len(normalized) > MAX_BATCH_QUERIES:
        raise ValueError(f"At most {MAX_BATCH_QUERIES} queries per batch.")

    return list(
        await asyncio.gather(
            *(search_concepts(q, group_ids=group_ids, limit=limit) for q in normalized)
        )
    )
