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
    bale_user_id: int | None = Field(
        default=None,
        nullable=True,
        index=True,
        unique=True,
        sa_type=sa.BigInteger,
    )

    first_name: str | None = Field(
        default=None,
        nullable=True,
    )
    last_name: str | None = Field(
        default=None,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, mobile={self.mobile}, bale_user_id={self.bale_user_id})"
