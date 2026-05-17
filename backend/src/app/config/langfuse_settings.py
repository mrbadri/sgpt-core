"""Environment-backed Langfuse settings (same `.env` source as Graphiti)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LangfuseSettings(BaseSettings):
    """Reads `LANGFUSE_*` from repo `infrastructure/.env` when cwd is `backend/`."""

    model_config = SettingsConfigDict(
        env_file=("./../infrastructure/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    environment: str = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    #: Preferred; overrides deprecated host when both are set.
    langfuse_base_url: str | None = None
    langfuse_host: str | None = None


@lru_cache
def get_langfuse_settings() -> LangfuseSettings:
    return LangfuseSettings()
