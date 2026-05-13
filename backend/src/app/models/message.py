"""BaleMessage model — records all inbound and outbound bot messages."""

from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import BaseDBModel


class BaleMessage(BaseDBModel, table=True):
    __tablename__ = "bale_message"  # type: ignore[assignment]

    bale_user_id: int = Field(
        nullable=False,
        index=True,
        sa_type=sa.BigInteger,
    )
    direction: str = Field(nullable=False, max_length=8)   # "in" | "out"
    message_type: str = Field(nullable=False, max_length=32)  # "text"|"command"|"contact"|"callback"|"error"|"status"
    content: str = Field(nullable=False, sa_type=sa.Text)
    raw_update_id: int | None = Field(default=None, nullable=True, sa_type=sa.BigInteger)

    def __repr__(self) -> str:
        snippet = self.content[:40].replace("\n", " ")
        return (
            f"BaleMessage(id={self.id}, user={self.bale_user_id}, "
            f"{self.direction}/{self.message_type}, '{snippet}')"
        )
