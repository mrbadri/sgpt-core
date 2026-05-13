"""Subscription and rate-limit service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.subscription import UserSubscription
from app.plans import PLAN_CONFIG


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _free_expiry() -> datetime:
    return datetime(9999, 1, 1)


def get_or_create_free(db: Session, bale_user_id: int) -> UserSubscription:
    """Return the user's subscription row, creating a free one if absent."""
    sub = db.exec(
        select(UserSubscription).where(UserSubscription.bale_user_id == bale_user_id)
    ).first()
    if sub is None:
        sub = UserSubscription(
            bale_user_id=bale_user_id,
            plan_key="free",
            duration_months=0,
            started_at=_now(),
            expires_at=_free_expiry(),
            budget_usd=PLAN_CONFIG["free"]["budget_usd"],
            used_usd=0.0,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


def check_rate_limit(db: Session, bale_user_id: int) -> tuple[bool, UserSubscription]:
    """Return (allowed, subscription).

    If a paid plan has expired, it is silently reset to free limits before checking.
    """
    sub = get_or_create_free(db, bale_user_id)
    now = _now()

    # Paid plan expired → reset to free limits (keep row, just downgrade)
    if sub.plan_key != "free" and sub.expires_at < now:
        sub.plan_key = "free"
        sub.duration_months = 0
        sub.expires_at = _free_expiry()
        sub.budget_usd = PLAN_CONFIG["free"]["budget_usd"]
        sub.used_usd = 0.0
        db.add(sub)
        db.commit()
        db.refresh(sub)

    allowed = sub.used_usd < sub.budget_usd
    return allowed, sub


def record_usage(db: Session, bale_user_id: int, cost_usd: float) -> None:
    """Add cost_usd to the user's accumulated usage."""
    if cost_usd <= 0:
        return
    sub = get_or_create_free(db, bale_user_id)
    sub.used_usd = round(sub.used_usd + cost_usd, 6)
    db.add(sub)
    db.commit()


def activate_plan(
    db: Session,
    bale_user_id: int,
    plan_key: str,
    duration_months: int,
    paid_irr: int = 0,
) -> UserSubscription:
    """Activate or upgrade a paid plan. Resets used_usd to 0, accumulates total_paid_irr."""
    sub = get_or_create_free(db, bale_user_id)
    now = _now()
    sub.plan_key = plan_key
    sub.duration_months = duration_months
    sub.started_at = now
    sub.expires_at = now + timedelta(days=30 * duration_months)
    sub.budget_usd = PLAN_CONFIG[plan_key]["budget_usd"]
    sub.used_usd = 0.0
    sub.total_paid_irr = (sub.total_paid_irr or 0) + paid_irr
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
