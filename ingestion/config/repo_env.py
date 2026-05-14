"""Load ``infrastructure/.env`` at the monorepo root for ingestion."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_INFRA_ENV_PATH = _REPO_ROOT / "infrastructure" / ".env"


def load_repo_dotenv() -> None:
    """Populate the process environment from ``infrastructure/.env`` if the file exists."""

    load_dotenv(_INFRA_ENV_PATH)
