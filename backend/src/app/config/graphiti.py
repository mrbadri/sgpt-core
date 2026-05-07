"""Environment-backed settings for Graphiti + FalkorDB (no side effects on import)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphitiSettings(BaseSettings):
    """Mirrors repo `.env.example` Graphiti / Falkor variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    graphiti_index_llm_base_url: str | None = None
    graphiti_index_llm_api_key: str | None = None
    graphiti_index_llm_model: str = Field(default="gpt-4o-mini")

    graphiti_index_reranker_base_url: str | None = None
    graphiti_index_reranker_api_key: str | None = None
    graphiti_index_reranker_model: str | None = None

    graphiti_index_embedding_base_url: str | None = None
    graphiti_index_embedding_api_key: str | None = None
    graphiti_index_embedding_model: str = Field(default="text-embedding-3-large")
    graphiti_index_embedding_dim: int = Field(default=3072)

    falkor_database: str = Field(default="exp_g11_bio_1404_4o_mini")
    falkor_host: str = Field(default="127.0.0.1")
    falkor_port: int = Field(default=6379)

    #: ``cross_encoder``: rerank via API (slower, often sharper). ``rrf``: reciprocal rank fusion (faster).
    graphiti_search_preset: Literal["cross_encoder", "rrf"] = Field(default="cross_encoder")
    #: Overrides recall breadth for Graphiti search (lower is faster). ``None`` uses ``DEFAULT_SEARCH_LIMIT``.
    graphiti_search_limit: int | None = Field(default=None)
    #: When true, the LangGraph tool keeps one ``Graphiti`` client open across searches (avoids reconnect cost).
    graphiti_search_reuse_client: bool = Field(default=True)


@lru_cache
def get_graphiti_settings() -> GraphitiSettings:
    return GraphitiSettings()
