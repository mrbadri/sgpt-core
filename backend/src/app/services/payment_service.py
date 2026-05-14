"""Payment service — persists payment transactions."""

from __future__ import annotations

from sqlmodel import Session

from app.models.payment import Payment


def record_payment(
    db: Session,
    *,
    user_id: str,
    provider: str,
    status: str = "success",
    plan_key: str,
    amount: int,
    currency: str,
    invoice_payload: str,
    provider_payment_charge_id: str,
) -> Payment:
    payment = Payment(
        user_id=user_id,
        provider=provider,
        status=status,
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
