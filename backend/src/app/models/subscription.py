"""UserSubscription model — tracks active plan and accumulated LLM cost per user."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import BaseDBModel


class UserSubscription(BaseDBModel, table=True):
    __tablename__ = "user_subscription"  # type: ignore[assignment]

    bale_user_id: int = Field(
        nullable=False,
        index=True,
        unique=True,
        sa_type=sa.BigInteger,
    )
    plan_key: str = Field(nullable=False, max_length=16)       # "free"|"basic"|"pro"
    duration_months: int = Field(nullable=False, default=0)    # 0 = free (no expiry)
    started_at: datetime = Field(nullable=False)
    expires_at: datetime = Field(nullable=False)               # year 9999 for free
    budget_usd: float = Field(nullable=False, default=0.0)
    used_usd: float = Field(nullable=False, default=0.0)
    total_paid_irr: int = Field(nullable=False, default=0)  # cumulative IRR paid across all activations

    def __repr__(self) -> str:
        return (
            f"UserSubscription(user={self.bale_user_id}, plan={self.plan_key}, "
            f"used={self.used_usd:.4f}/{self.budget_usd}, "
            f"paid={self.total_paid_irr:,} IRR, expires={self.expires_at.date()})"
        )
