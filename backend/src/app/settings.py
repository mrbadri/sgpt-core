"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Bale Bot Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/bale_bot"
    database_echo: bool = False

    # Bale Bot API
    bale_bot_token: Optional[str] = None
    bale_api_url: str = "https://tapi.bale.ai/bot{0}/{1}"
    bale_bot_phone: Optional[str] = None

    # Admin Authentication
    admin_secret_key: Optional[str] = None
    admin_token_expire_minutes: int = 60 * 24  # 24 hours

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


settings = Settings()
