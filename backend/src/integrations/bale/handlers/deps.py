"""Dependency bundle for Bale message handlers."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

import telebot
from telebot import types

from app.services.agent_bridge import BaleAgentBridge

# Shared thread pool — fire-and-forget DB writes never block the bot
_msg_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bale_msg_log")


def log_bale_incoming(handler: str, **fields: object) -> None:
    """Structured stdout banner for local debugging (docker logs, dev)."""
    bar = "=" * 72
    print(bar)
    print(f"[bale] {handler}")
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", "\\n")
        if len(text) > 240:
            text = text[:237] + "..."
        print(f"  {key}: {text}")
    print(bar)


def _persist_message(
    bale_user_id: int,
    direction: str,
    message_type: str,
    content: str,
    raw_update_id: int | None,
) -> None:
    """Run inside the thread pool — opens its own DB session."""
    try:
        from app.db.session import get_db_session
        from app.services import message_service

        db = get_db_session()
        try:
            message_service.record(
                db,
                bale_user_id=bale_user_id,
                direction=direction,
                message_type=message_type,
                content=content,
                raw_update_id=raw_update_id,
            )
        finally:
            db.close()
    except Exception:
        pass  # logging failures must never affect the bot response


@dataclass(frozen=True)
class BaleHandlerDeps:
    bot: telebot.TeleBot
    logger: logging.Logger
    agent_bridge: BaleAgentBridge
    reply_long_text: Callable[[types.Message, str], None]
    payment_provider_token: str = ""
    api_url: str = "https://tapi.bale.ai/bot{0}/{1}"

    def log_message(
        self,
        bale_user_id: int,
        direction: str,
        message_type: str,
        content: str,
        raw_update_id: int | None = None,
    ) -> None:
        """Fire-and-forget: persist a message to DB without blocking."""
        _msg_executor.submit(
            _persist_message,
            bale_user_id,
            direction,
            message_type,
            content,
            raw_update_id,
        )
