"""Graphiti factory: Neo4j driver + OpenAI-compatible LLM, embedder, reranker."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client import OpenAIClient, LLMConfig

from graphiti_core.driver.neo4j_driver import Neo4jDriver

from config.falkordb import FALKOR_DATABASE, create_falkor_driver

# --- env ---------------------------------------------------------------------------
load_dotenv()

# LLM for Graphiti indexing (OpenAI-compatible)
GRAPHITI_INDEX_LLM_BASE_URL = os.getenv("GRAPHITI_INDEX_LLM_BASE_URL")
GRAPHITI_INDEX_LLM_API_KEY = os.getenv("GRAPHITI_INDEX_LLM_API_KEY")
GRAPHITI_INDEX_LLM_MODEL = os.getenv("GRAPHITI_INDEX_LLM_MODEL", "gpt-4o-mini")

# Reranker / cross-encoder (optional; each falls back to the corresponding GRAPHITI_INDEX_LLM_* value)
GRAPHITI_INDEX_RERANKER_BASE_URL =  os.getenv("GRAPHITI_INDEX_RERANKER_BASE_URL")
GRAPHITI_INDEX_RERANKER_API_KEY =  os.getenv("GRAPHITI_INDEX_RERANKER_API_KEY")
GRAPHITI_INDEX_RERANKER_MODEL =   os.getenv("GRAPHITI_INDEX_RERANKER_MODEL")

# Embeddings for Graphiti indexing
GRAPHITI_INDEX_EMBEDDING_BASE_URL = os.getenv("GRAPHITI_INDEX_EMBEDDING_BASE_URL")
GRAPHITI_INDEX_EMBEDDING_API_KEY = os.getenv("GRAPHITI_INDEX_EMBEDDING_API_KEY")
GRAPHITI_INDEX_EMBEDDING_MODEL = os.getenv(
    "GRAPHITI_INDEX_EMBEDDING_MODEL", "text-embedding-3-large"
)
GRAPHITI_INDEX_EMBEDDING_DIM = int(os.getenv("GRAPHITI_INDEX_EMBEDDING_DIM", 3072))

# Cross-encoder reranker: OpenAI sends ``logit_bias`` by default; many compatible gateways reject it.
GRAPHITI_RERANKER_USE_LOGIT_BIAS = (
    os.getenv("GRAPHITI_RERANKER_USE_LOGIT_BIAS", "").strip().lower() in ("1", "true", "yes")
)

# Validate required environment variables
if not GRAPHITI_INDEX_LLM_API_KEY or not GRAPHITI_INDEX_EMBEDDING_API_KEY:
    raise ValueError(
        "Set GRAPHITI_INDEX_LLM_API_KEY and GRAPHITI_INDEX_EMBEDDING_API_KEY "
        "for Graphiti indexing (LLM, embedder, reranker)."
    )

# LLM client
llm_config = LLMConfig(
    api_key=GRAPHITI_INDEX_LLM_API_KEY,
    base_url=GRAPHITI_INDEX_LLM_BASE_URL,
    model=GRAPHITI_INDEX_LLM_MODEL,
)

llm_client = OpenAIClient(config=llm_config)

# Reranker client
reranker_config = LLMConfig(
    api_key=GRAPHITI_INDEX_RERANKER_API_KEY,
    base_url=GRAPHITI_INDEX_RERANKER_BASE_URL,
    model=GRAPHITI_INDEX_RERANKER_MODEL,
)

reranker_client = OpenAIRerankerClient(config=reranker_config)



# Embedder
embedder = OpenAIEmbedder(
    config=OpenAIEmbedderConfig(
        api_key=GRAPHITI_INDEX_EMBEDDING_API_KEY,
        base_url=GRAPHITI_INDEX_EMBEDDING_BASE_URL,
        embedding_model=GRAPHITI_INDEX_EMBEDDING_MODEL,
        embedding_dim=GRAPHITI_INDEX_EMBEDDING_DIM,
    )
)


def create_graphiti(**overrides) -> Graphiti:
    """Return Graphiti with our Neo4j DB and clients; ``overrides`` map to ``Graphiti(...)`` kwargs."""
    

    driver = create_falkor_driver()

    return Graphiti(
        graph_driver=driver,
        embedder=embedder,
        llm_client=llm_client,
        cross_encoder=reranker_client,
        **overrides,
    )
