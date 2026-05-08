"""User linking for Bale (mobile + bale_user_id on User)."""

from __future__ import annotations

from typing import Literal

from sqlmodel import Session, select

from app.models.user import User


def normalize_mobile_from_contact(phone_number: str) -> int | None:
    """Normalize contact phone to national mobile digits (no leading country/zero)."""
    clean = phone_number.lstrip("+")
    if clean.startswith("00"):
        clean = clean[2:]
    if clean.startswith("98"):
        clean = clean[2:]
    clean = clean.lstrip("0")
    return int(clean) if clean.isdigit() else None


def unregister_stale_bale_links(session: Session, bale_tid: int, mobile: int) -> None:
    """Clear bale_user_id on other rows so one Bale account can link to a new mobile."""
    stale = session.exec(
        select(User).where(
            User.bale_user_id == bale_tid,
            User.mobile != mobile,
        )
    ).all()
    for row in stale:
        row.bale_user_id = None
        session.add(row)


def commit_user_for_bale_contact(
    session: Session,
    mobile: int,
    bale_tid: int,
) -> tuple[Literal["created", "linked"], User]:
    """
    Link bale_user_id to the user with this mobile, creating a row if needed.
    Caller is responsible for try/except, rollback, and session lifecycle.
    """
    unregister_stale_bale_links(session, bale_tid, mobile)
    existing = session.exec(select(User).where(User.mobile == mobile)).first()
    if existing:
        existing.bale_user_id = int(bale_tid)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return ("linked", existing)
    user = User.model_validate({"mobile": mobile, "bale_user_id": int(bale_tid)})
    session.add(user)
    session.commit()
    session.refresh(user)
    return ("created", user)


def fetch_user_by_bale_user_id(session: Session, bale_tid: int) -> User | None:
    return session.exec(select(User).where(User.bale_user_id == bale_tid)).first()
