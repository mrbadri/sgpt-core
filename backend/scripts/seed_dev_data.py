"""Seed development database with test data."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.db.base import Base


def seed_database(db: Session) -> None:
    """Seed the database with development data."""
    # TODO: Implement seed data logic
    # This should create test groups, leaders, members, invites, etc.
    print("Seeding development database...")
    print("TODO: Implement seed data logic")
    pass


def main() -> None:
    """Main entry point."""
    db = next(get_db_session())
    try:
        seed_database(db)
        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
