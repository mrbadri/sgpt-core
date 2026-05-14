"""Message model — records all inbound and outbound bot messages across channels."""

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlmodel import Field, Relationship

from app.models.base import BaseDBModelUUID

if TYPE_CHECKING:
    from app.models.user import User


class Message(BaseDBModelUUID, table=True):
    __tablename__ = "message"  # type: ignore[assignment]

    user_id: str | None = Field(
        default=None,
        nullable=True,
        foreign_key="user.id",
        index=True,
    )
    channel: str = Field(
        nullable=False,
        max_length=32,
        sa_column_kwargs={"comment": "bale | web | telegram"},
    )
    direction: str = Field(nullable=False, max_length=8)    # "in" | "out"
    message_type: str = Field(nullable=False, max_length=32)  # "text"|"command"|"contact"|"callback"|"error"|"status"
    content: str = Field(nullable=False, sa_type=sa.Text)
    raw_update_id: int | None = Field(default=None, nullable=True, sa_type=sa.BigInteger)

    user: Optional["User"] = Relationship(back_populates="messages")

    def __repr__(self) -> str:
        snippet = self.content[:40].replace("\n", " ")
        return (
            f"Message(id={self.id}, user={self.user_id}, channel={self.channel}, "
            f"{self.direction}/{self.message_type}, '{snippet}')"
        )


# Backward-compat alias so any stale import of BaleMessage still resolves
BaleMessage = Message
