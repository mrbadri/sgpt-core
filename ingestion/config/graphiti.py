"""Graphiti factory: Neo4j driver + OpenAI-compatible LLM, embedder, reranker."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client import OpenAIClient, LLMConfig

from ingestion.lib.embedding import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_MODEL,
    GAPGPT_BASE_URL,
)

# --- env ---------------------------------------------------------------------------

load_dotenv()

_DEFAULT_NEO4J_DATABASE = "neo4j"
_DEFAULT_LLM_MODEL = "gpt-4o-mini"


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", _DEFAULT_NEO4J_DATABASE)

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")

# Validate required environment variables
if not LLM_BASE_URL or not EMBEDDING_API_KEY:
    raise ValueError("Set LLM_API_KEY and EMBEDDING_API_KEY for Graphiti embedder, LLM, and reranker.")

# Create LLM client
llm_config = LLMConfig(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    model=os.getenv("LLM_MODEL", _DEFAULT_LLM_MODEL),
)

llm_client = OpenAIClient(config=llm_config)
reranker_client = OpenAIRerankerClient(config=llm_config)

# Create embedding client
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIMENSION)))

embedder = OpenAIEmbedder(
    config=OpenAIEmbedderConfig(
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
        embedding_model=EMBEDDING_MODEL,
        embedding_dim=EMBEDDING_DIM,
    )
)


def create_graphiti(**overrides) -> Graphiti:
    """Return Graphiti with our Neo4j DB and clients; ``overrides`` map to ``Graphiti(...)`` kwargs."""
    
    # Create Neo4j driver
    driver = Neo4jDriver(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )
    return Graphiti(
        graph_driver=driver,
        embedder=embedder,
        llm_client=llm_client,
        cross_encoder=reranker_client,
        **overrides,
    )
