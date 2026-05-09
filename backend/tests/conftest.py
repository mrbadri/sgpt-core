"""Pytest configuration and fixtures."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlmodel import Session

from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.models import User  # noqa: F401 — register User metadata for create_all


def _test_database_url() -> str:
    """Prefer TEST_DATABASE_URL, then DATABASE_URL, else in-memory SQLite for local runs."""
    return (
        os.getenv("TEST_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "sqlite:///:memory:"
    )


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    url = _test_database_url()
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine):
    """Create test database session with transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection, class_=Session
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Only rollback if transaction is still active
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)
