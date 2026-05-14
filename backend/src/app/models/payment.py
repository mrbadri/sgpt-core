"""Payment model — records payment transactions across providers."""

from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import BaseDBModelUUID


class Payment(BaseDBModelUUID, table=True):
    __tablename__ = "payment"  # type: ignore[assignment]

    user_id: str = Field(
        nullable=False,
        foreign_key="user.id",
        index=True,
    )
    provider: str = Field(
        nullable=False,
        max_length=32,
        sa_column_kwargs={"comment": "bale | zarinpal | stripe"},
    )
    status: str = Field(
        nullable=False,
        max_length=16,
        default="success",
        sa_column_kwargs={"comment": "pending | success | failed"},
    )
    plan_key: str = Field(nullable=False, max_length=64)
    amount: int = Field(nullable=False, sa_type=sa.BigInteger)
    currency: str = Field(default="IRR", nullable=False, max_length=8)
    invoice_payload: str = Field(nullable=False, max_length=256)
    provider_payment_charge_id: str = Field(nullable=False, max_length=256)

    def __repr__(self) -> str:
        return (
            f"Payment(id={self.id}, user_id={self.user_id}, provider={self.provider}, "
            f"plan={self.plan_key}, amount={self.amount}, status={self.status})"
        )


# Backward-compat alias
BalePayment = Payment
