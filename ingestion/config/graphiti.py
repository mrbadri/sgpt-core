"""Neo4j and LLM configuration"""

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

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# Default graph name on the server. Extra DBs on one instance need Neo4j that allows them (often Enterprise).
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

_GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")
if not _GAPGPT_API_KEY:
    raise ValueError(
        "GapGPT API key required for Graphiti embedder and LLM: set GAPGPT_API_KEY",
    )

# LLM uses the same OpenAI-compatible stack; base URL from .env (e.g. GEMINI_BASE_URL) or GapGPT default.
_LLM_BASE_URL = os.getenv("LLM_BASE_URL") or GAPGPT_BASE_URL

_GRAPHITI_LLM_CONFIG = LLMConfig(
    api_key=_GAPGPT_API_KEY,
    base_url=_LLM_BASE_URL,
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
)

LLM_CLIENT = OpenAIClient(config=_GRAPHITI_LLM_CONFIG)
GRAPHITI_CROSS_ENCODER = OpenAIRerankerClient(config=_GRAPHITI_LLM_CONFIG)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIMENSION)))

GRAPHITI_EMBEDDER = OpenAIEmbedder(
    config=OpenAIEmbedderConfig(
        api_key=_GAPGPT_API_KEY,
        base_url=GAPGPT_BASE_URL,
        embedding_model=EMBEDDING_MODEL,
        embedding_dim=EMBEDDING_DIM,
    )
)


def create_graphiti(**graphiti_kwargs) -> Graphiti:
    """Graphiti wired to Neo4j; set NEO4J_DATABASE per project when the server supports multiple DBs."""
    driver = Neo4jDriver(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )
    merged = {
        "graph_driver": driver,
        "embedder": GRAPHITI_EMBEDDER,
        "llm_client": LLM_CLIENT,
        "cross_encoder": GRAPHITI_CROSS_ENCODER,
    }
    merged.update(graphiti_kwargs)
    return Graphiti(**merged)
