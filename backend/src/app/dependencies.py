"""Dependency injection for FastAPI."""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()
