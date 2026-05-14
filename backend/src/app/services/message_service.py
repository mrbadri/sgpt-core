"""Service for persisting bot messages to the database."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.message import BaleMessage
from app.models.user import User


def record(
    db: Session,
    bale_user_id: int,
    direction: str,
    message_type: str,
    content: str,
    raw_update_id: int | None = None,
) -> BaleMessage:
    user = db.exec(select(User).where(User.bale_user_id == bale_user_id)).first()
    msg = BaleMessage(
        user_id=user.id if user else None,
        bale_user_id=bale_user_id,
        direction=direction,
        message_type=message_type,
        content=content,
        raw_update_id=raw_update_id,
    )
    db.add(msg)
    db.commit()
    return msg
