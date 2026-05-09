"""Logging configuration."""

import logging
import sys
from typing import Any

from app.settings import settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.log_format == "json":
        # JSON logging for production
        # TODO: Integrate with json_logging or structured logging library
        # For now, use structured format
        logging.basicConfig(
            level=log_level,
            format='{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
            handlers=[logging.StreamHandler(sys.stdout)],
        )
    else:
        # Human-readable logging for development
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
