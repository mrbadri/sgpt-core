"""Payment service — persists successful Bale payments."""

from __future__ import annotations

from sqlmodel import Session

from app.models.payment import BalePayment


def record_payment(
    db: Session,
    *,
    bale_user_id: int,
    plan_key: str,
    amount: int,
    currency: str,
    invoice_payload: str,
    provider_payment_charge_id: str,
) -> BalePayment:
    payment = BalePayment(
        bale_user_id=bale_user_id,
        plan_key=plan_key,
        amount=amount,
        currency=currency,
        invoice_payload=invoice_payload,
        provider_payment_charge_id=provider_payment_charge_id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
