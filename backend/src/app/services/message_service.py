"""Service for persisting bot messages to the database."""

from __future__ import annotations

from sqlmodel import Session

from app.models.message import BaleMessage


def record(
    db: Session,
    bale_user_id: int,
    direction: str,
    message_type: str,
    content: str,
    raw_update_id: int | None = None,
) -> BaleMessage:
    msg = BaleMessage(
        bale_user_id=bale_user_id,
        direction=direction,
        message_type=message_type,
        content=content,
        raw_update_id=raw_update_id,
    )
    db.add(msg)
    db.commit()
    return msg
