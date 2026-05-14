"""User model."""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlmodel import Field, Relationship

from app.models.base import BaseDBModelUUID

if TYPE_CHECKING:
    from app.models.message import Message


class User(BaseDBModelUUID, table=True):
    __tablename__ = "user"  # type: ignore[assignment]

    mobile: int | None = Field(
        default=None,
        nullable=True,
        index=True,
        unique=True,
        sa_type=sa.BigInteger,
    )
    email: str | None = Field(
        default=None,
        nullable=True,
        index=True,
        unique=True,
        max_length=255,
    )
    first_name: str | None = Field(default=None, nullable=True)
    last_name: str | None = Field(default=None, nullable=True)

    messages: list["Message"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, mobile={self.mobile}, email={self.email})"
