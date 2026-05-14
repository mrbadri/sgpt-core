"""UserIdentity model — maps canonical users.id to platform-specific credentials."""

from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Field, UniqueConstraint

from app.models.base import BaseDBModelUUID


class UserIdentity(BaseDBModelUUID, table=True):
    __tablename__ = "user_identity"  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_identity_provider"),)

    user_id: str = Field(
        nullable=False,
        foreign_key="user.id",
        index=True,
    )
    provider: str = Field(
        nullable=False,
        max_length=32,
        sa_column_kwargs={"comment": "bale | web | telegram"},
    )
    provider_user_id: str = Field(
        nullable=False,
        max_length=128,
        sa_column_kwargs={"comment": "platform-specific user identifier as string"},
    )

    def __repr__(self) -> str:
        return f"UserIdentity(user_id={self.user_id}, provider={self.provider}, pid={self.provider_user_id})"
