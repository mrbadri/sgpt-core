"""User model."""

from sqlmodel import Field

from app.models.base import BaseDBModelUUID


class User(BaseDBModelUUID, table=True):
    __tablename__ = "user"  # type: ignore[assignment]

    mobile: str = Field(
        unique=True,
        nullable=False,
        max_length=20,
        index=True,
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, mobile={self.mobile})"
