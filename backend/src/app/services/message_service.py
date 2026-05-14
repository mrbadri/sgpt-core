"""Service for persisting bot messages to the database."""

from __future__ import annotations

from sqlmodel import Session

from app.models.message import Message


def record(
    db: Session,
    user_id: str | None,
    channel: str,
    direction: str,
    message_type: str,
    content: str,
    raw_update_id: int | None = None,
) -> Message:
    msg = Message(
        user_id=user_id,
        channel=channel,
        direction=direction,
        message_type=message_type,
        content=content,
        raw_update_id=raw_update_id,
    )
    db.add(msg)
    db.commit()
    return msg
