"""Database session management."""

from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from app.settings import settings


# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


# Session factory for compatibility with legacy code that uses SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db_session() -> Session:
    """Get a database session."""
    return Session(engine)


def init_db() -> None:
    """Initialize database tables."""
    SQLModel.metadata.create_all(bind=engine)
