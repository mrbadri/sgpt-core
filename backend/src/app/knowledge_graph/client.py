"""Construct a ``Graphiti`` instance with Falkor + OpenAI-compatible clients."""

from __future__ import annotations

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client import LLMConfig, OpenAIClient

from app.config.graphiti import get_graphiti_settings
from app.knowledge_graph.falkordb import create_falkor_driver


def create_graphiti(**overrides) -> Graphiti:
    """Build Graphiti; validates required API keys at call time (not on import)."""

    s = get_graphiti_settings()
    if not s.graphiti_index_llm_api_key or not s.graphiti_index_embedding_api_key:
        raise ValueError(
            "Set GRAPHITI_INDEX_LLM_API_KEY and GRAPHITI_INDEX_EMBEDDING_API_KEY "
            "for Graphiti (LLM, embedder, reranker)."
        )

    llm_config = LLMConfig(
        api_key=s.graphiti_index_llm_api_key,
        base_url=s.graphiti_index_llm_base_url,
        model=s.graphiti_index_llm_model,
    )
    llm_client = OpenAIClient(config=llm_config)

    rer_key = s.graphiti_index_reranker_api_key or s.graphiti_index_llm_api_key
    rer_base = s.graphiti_index_reranker_base_url or s.graphiti_index_llm_base_url
    rer_model = s.graphiti_index_reranker_model or s.graphiti_index_llm_model
    reranker_config = LLMConfig(
        api_key=rer_key,
        base_url=rer_base,
        model=rer_model,
    )
    reranker_client = OpenAIRerankerClient(config=reranker_config)

    embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key=s.graphiti_index_embedding_api_key,
            base_url=s.graphiti_index_embedding_base_url,
            embedding_model=s.graphiti_index_embedding_model,
            embedding_dim=s.graphiti_index_embedding_dim,
        )
    )

    driver = create_falkor_driver()

    return Graphiti(
        graph_driver=driver,
        embedder=embedder,
        llm_client=llm_client,
        cross_encoder=reranker_client,
        **overrides,
    )
