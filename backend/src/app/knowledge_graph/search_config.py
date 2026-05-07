"""Search presets aligned with ``ingestion.examples.graphiti_search_conceptual_example``."""

from __future__ import annotations

from graphiti_core.search.search_config import EdgeSearchMethod, NodeSearchMethod
from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    COMBINED_HYBRID_SEARCH_RRF,
)

DEFAULT_SEARCH_LIMIT = 20
RESULT_LIMIT_PER_CATEGORY = 20


def search_config_rrf_no_bfs(limit: int = DEFAULT_SEARCH_LIMIT):
    """Hybrid search with RRF reranking (no cross-encoder API round-trip; faster than cross_encoder preset)."""

    return COMBINED_HYBRID_SEARCH_RRF.model_copy(update={"limit": limit})


def search_config_cross_encoder_no_bfs(limit: int = DEFAULT_SEARCH_LIMIT):
    """Hybrid + cross-encoder reranking without edge/node BFS (avoids Falkor timeouts)."""

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
