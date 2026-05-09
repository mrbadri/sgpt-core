"""LangChain tool wrapping Graphiti conceptual search."""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from app.knowledge_graph.search import (
    ConceptSearchResult,
    nonempty_batch_queries,
    search_concepts,
    search_concepts_batch,
)


def _format_concept_search_result(
    res: ConceptSearchResult,
    *,
    max_episode_chars: int,
) -> str:
    blocks: list[str] = []
    for i, edge in enumerate(res.edges, start=1):
        blocks.append(f"Fact {i} [{edge.name}]: {edge.fact}")

    for i, ep in enumerate(res.episodes, start=1):
        text = ep.content or ""
        if len(text) > max_episode_chars:
            text = text[:max_episode_chars] + "…"
        blocks.append(f"Chunk {i}: {text}")

    return "\n\n".join(blocks) if blocks else "No matching facts or chunks were retrieved."


def build_graphiti_search_tool(*, max_episode_chars: int = 1500) -> BaseTool:
    """Return a fresh ``search_knowledge_graph`` tool (configurable truncation)."""

    @tool
    async def search_knowledge_graph(query: str, group_ids: str | None = None) -> str:
        """Search the Graphiti memory graph for relational facts and source chunks (episodes).

        Use this when you need grounded snippets from ingested documents.

        Args:
            query: Natural-language question or search string (Persian or English).
            group_ids: Optional comma-separated group IDs (underscores recommended; hyphens can break Falkor fulltext filters).
        """
        gid_list = None
        if group_ids and group_ids.strip():
            gid_list = [p.strip() for p in group_ids.split(",") if p.strip()]

        res = await search_concepts(query, group_ids=gid_list)

        return _format_concept_search_result(res, max_episode_chars=max_episode_chars)

    return search_knowledge_graph


def build_graphiti_batch_search_tool(*, max_episode_chars: int = 1500) -> BaseTool:
    """Return a ``search_knowledge_graph_batch`` tool (concurrent multi-query search)."""

    @tool
    async def search_knowledge_graph_batch(
        queries: list[str],
        group_ids: str | None = None,
    ) -> str:
        """Search the knowledge graph for several independent questions at once (runs in parallel).

        Prefer this when you need multiple separate lookups from the course materials instead of
        calling the single-query tool repeatedly.

        Args:
            queries: One or more natural-language questions or search strings (Persian or English).
            group_ids: Optional comma-separated group IDs (underscores recommended; hyphens can break Falkor fulltext filters).
        """
        gid_list = None
        if group_ids and group_ids.strip():
            gid_list = [p.strip() for p in group_ids.split(",") if p.strip()]

        results = await search_concepts_batch(queries, group_ids=gid_list)

        labels = nonempty_batch_queries(queries)

        sections: list[str] = []
        for label, res in zip(labels, results, strict=True):
            body = _format_concept_search_result(res, max_episode_chars=max_episode_chars)
            sections.append(f"### Query: {label}\n\n{body}")

        return "\n\n---\n\n".join(sections)

    return search_knowledge_graph_batch
