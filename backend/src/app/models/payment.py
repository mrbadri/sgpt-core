"""BalePayment model — records successful Bale wallet transactions."""

from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import BaseDBModel


class BalePayment(BaseDBModel, table=True):
    __tablename__ = "bale_payment"  # type: ignore[assignment]

    bale_user_id: int = Field(
        nullable=False,
        index=True,
        sa_type=sa.BigInteger,
    )
    plan_key: str = Field(nullable=False, max_length=64)
    amount: int = Field(nullable=False, sa_type=sa.BigInteger)
    currency: str = Field(default="IRR", nullable=False, max_length=8)
    invoice_payload: str = Field(nullable=False, max_length=256)
    provider_payment_charge_id: str = Field(nullable=False, max_length=256)

    def __repr__(self) -> str:
        return (
            f"BalePayment(id={self.id}, bale_user_id={self.bale_user_id}, "
            f"plan={self.plan_key}, amount={self.amount})"
        )
