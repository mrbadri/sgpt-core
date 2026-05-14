"""User identity service — resolves and creates platform identities linked to canonical users."""

from __future__ import annotations

import uuid
from typing import Literal

from sqlmodel import Session, select

from app.models.identity import UserIdentity
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


def fetch_user_by_identity(session: Session, provider: str, provider_user_id: str) -> User | None:
    """Return the canonical User for a (provider, provider_user_id) pair, or None."""
    identity = session.exec(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_user_id == provider_user_id,
        )
    ).first()
    if identity is None:
        return None
    return session.get(User, identity.user_id)


def _unregister_stale_identities(session: Session, provider: str, provider_user_id: str, mobile: int) -> None:
    """Remove existing identity rows for this provider/pid that point to a different mobile."""
    identity = session.exec(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_user_id == provider_user_id,
        )
    ).first()
    if identity is None:
        return
    user = session.get(User, identity.user_id)
    if user and user.mobile != mobile:
        session.delete(identity)


def commit_user_for_bale_contact(
    session: Session,
    mobile: int,
    bale_tid: int,
) -> tuple[Literal["created", "linked"], User]:
    """
    Link bale_tid to the user with this mobile (creating a User row if needed).
    Creates or updates a UserIdentity row with provider='bale'.
    Caller is responsible for try/except, rollback, and session lifecycle.
    """
    provider = "bale"
    pid = str(bale_tid)

    _unregister_stale_identities(session, provider, pid, mobile)

    existing_user = session.exec(select(User).where(User.mobile == mobile)).first()
    if existing_user is None:
        existing_user = User(id=str(uuid.uuid4()), mobile=mobile)
        session.add(existing_user)
        session.flush()
        status: Literal["created", "linked"] = "created"
    else:
        status = "linked"

    # Upsert identity row
    identity = session.exec(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_user_id == pid,
        )
    ).first()
    if identity is None:
        identity = UserIdentity(
            id=str(uuid.uuid4()),
            user_id=existing_user.id,
            provider=provider,
            provider_user_id=pid,
        )
        session.add(identity)
    elif identity.user_id != existing_user.id:
        identity.user_id = existing_user.id
        session.add(identity)

    session.commit()
    session.refresh(existing_user)
    return (status, existing_user)


# Legacy shim for any code that hasn't migrated yet
def fetch_user_by_bale_user_id(session: Session, bale_tid: int) -> User | None:
    return fetch_user_by_identity(session, "bale", str(bale_tid))
