"""
Base models for all database tables.
Contains shared fields and utility methods.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig

# ==================== Base Classes ====================


class TimestampMixin(SQLModel):
    """
    Mixin برای اضافه کردن timestamp های ایجاد و آپدیت.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )


class SoftDeleteMixin(SQLModel):
    """
    Mixin برای soft delete (حذف نرم افزاری).
    """

    is_deleted: bool = Field(default=False, nullable=False)
    deleted_at: datetime | None = Field(default=None, nullable=True)


class UUIDBase(SQLModel):
    """
    کلاس پایه برای مدل‌هایی که از UUID به عنوان primary key استفاده می‌کنند.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        max_length=36,
        nullable=False,
    )


class IntegerIDBase(SQLModel):
    """
    کلاس پایه برای مدل‌هایی که از Integer به عنوان primary key استفاده می‌کنند.
    """

    id: int = Field(
        default=None,
        primary_key=True,
        index=True,
    )


# ==================== Main Base Model ====================


class BaseDBModel(IntegerIDBase, TimestampMixin):
    """
    کلاس پایه اصلی برای تمام مدل‌های دیتابیس.
    شامل: ID, created_at, updated_at

    استفاده:
        class User(BaseDBModel, table=True):
            __tablename__ = "users"
            name: str
            email: str
    """

    model_config = SQLModelConfig(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def dict(self, **kwargs):
        """Override dict method for custom serialization."""
        return super().model_dump(**kwargs)

    def __repr__(self) -> str:
        """String representation of model."""
        class_name = self.__class__.__name__
        attrs = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"{class_name}({attrs})"


class BaseDBModelWithSoftDelete(BaseDBModel, SoftDeleteMixin):
    """
    کلاس پایه با قابلیت soft delete.
    شامل: ID, created_at, updated_at, is_deleted, deleted_at

    استفاده:
        class Post(BaseDBModelWithSoftDelete, table=True):
            __tablename__ = "posts"
            title: str
            content: str
    """

    def soft_delete(self):
        """Mark record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        """Restore soft deleted record."""
        self.is_deleted = False
        self.deleted_at = None

    @classmethod
    def active_only(cls):
        """Query helper برای فقط رکوردهای فعال."""
        from sqlmodel import select

        return select(cls).where(cls.is_deleted == False)


class BaseDBModelUUID(UUIDBase, TimestampMixin):
    """
    کلاس پایه با UUID primary key.
    شامل: UUID id, created_at, updated_at
    """

    model_config = SQLModelConfig(
        from_attributes=True,
        validate_assignment=True,
    )


# ==================== Export All ====================

__all__ = [
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDBase",
    "IntegerIDBase",
    "BaseDBModel",
    "BaseDBModelWithSoftDelete",
    "BaseDBModelUUID",
]
