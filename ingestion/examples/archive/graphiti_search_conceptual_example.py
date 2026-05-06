"""Run a conceptual search against Graphiti for biology chapter 3 splits.

The query targets the blood-brain barrier section of
``ingestion/data/prepare/exp-g11-bio/chapter_3/split-docs-main-2.json``.

Uses the advanced ``search_()`` API so that entity edges AND the raw episode
chunks are both returned — the two key facts about which substances can/cannot
cross the barrier live in episodes, not in extracted edges.

With FalkorDB, the stock ``COMBINED_HYBRID_SEARCH_CROSS_ENCODER`` recipe enables
BFS over relationships; large ``limit`` values can trigger Redis query timeouts.
This script uses the same hybrid + cross-encoder reranking **without** edge/node
BFS (BM25 + cosine only for graph entities).

Prerequisite: load that JSON into Neo4j with the same ``group_id``::

    uv run python -m ingestion.graph.graph

Needs the same env as ``ingestion.config.graphiti`` (Neo4j, LLM, embeddings).

From the repository root::

    uv run python -m ingestion.examples.graphiti_search_conceptual_example
"""

from __future__ import annotations

import asyncio

from graphiti_core.search.search_config import EdgeSearchMethod, NodeSearchMethod
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_CROSS_ENCODER

from ingestion.config.graphiti import create_graphiti

# Underscores: FalkorDB fulltext uses RediSearch; hyphens in group_id break @group_id: filters.
# GROUP_ID = "exp_g11_bio_chapter_3_4o"

SEARCH_LIMIT = 100


def search_config_cross_encoder_no_bfs(limit: int = SEARCH_LIMIT):
    """Like ``COMBINED_HYBRID_SEARCH_CROSS_ENCODER`` but without edge/node BFS.

    FalkorDB can hit Redis ``Query timed out`` on variable-length ``RELATES_TO|MENTIONS*``
    traversals when the candidate ``limit`` is large; BM25 + cosine + cross-encoder is
    enough for this textbook demo.
    """
    base = COMBINED_HYBRID_SEARCH_CROSS_ENCODER
    edge_cfg = base.edge_config
    node_cfg = base.node_config
    assert edge_cfg is not None and node_cfg is not None
    return base.model_copy(
        update={
            "limit": limit,
            "edge_config": edge_cfg.model_copy(
                update={
                    "search_methods": [
                        EdgeSearchMethod.bm25,
                        EdgeSearchMethod.cosine_similarity,
                    ],
                },
            ),
            "node_config": node_cfg.model_copy(
                update={
                    "search_methods": [
                        NodeSearchMethod.bm25,
                        NodeSearchMethod.cosine_similarity,
                    ],
                },
            ),
        },
    )


CONCEPTUAL_QUERY = (
    "عوامل حفاظتی از مغز رو نام ببر"
    # "سد خونی-مغزی چگونه از مغز در برابر مواد مضر و میکروب‌ها محافظت می‌کند "
    # "و چه موادی می‌توانند از این سد عبور کنند؟"
)


def _normalize(text: str) -> str:
    """Collapse whitespace so minor formatting differences don't cause duplicates."""
    return " ".join(text.split())


def _unique(items, key_fn):
    seen: set[str] = set()
    result = []
    for item in items:
        k = _normalize(key_fn(item))
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


async def main() -> None:
    graphiti = create_graphiti()
    search_config = search_config_cross_encoder_no_bfs()
    try:
        results = await graphiti.search_(
            CONCEPTUAL_QUERY,
            config=search_config,
            # group_ids=[GROUP_ID],
        )

        edges = _unique(results.edges, lambda e: e.fact)
        episodes = _unique(results.episodes, lambda ep: ep.content)

        print("پرسش مفهومی:")
        print(CONCEPTUAL_QUERY)

        print(f"\n{'='*60}")
        print(f"یال‌های موجودیت (facts): {len(edges)}")
        print('='*60)
        for i, edge in enumerate(edges, start=1):
            print(f"\n{i}. [{edge.name}]\n   {edge.fact}")

        print(f"\n{'='*60}")
        print(f"chunk‌های متنی (episodes): {len(episodes)}")
        print('='*60)
        for i, ep in enumerate(episodes, start=1):
            print(f"\n{i}. {ep.content}")

    finally:
        await graphiti.close()


if __name__ == "__main__":
    asyncio.run(main())
