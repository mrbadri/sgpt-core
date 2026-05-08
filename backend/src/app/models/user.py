"""User model."""

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import BaseDBModelUUID


class User(BaseDBModelUUID, table=True):
    __tablename__ = "user"  # type: ignore[assignment]

    mobile: int = Field(
        nullable=False,
        index=True,
        unique=True,
        sa_type=sa.BigInteger,
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, mobile={self.mobile})"
