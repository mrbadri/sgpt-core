"""Dependency bundle for Bale message handlers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

import telebot
from telebot import types

from app.services.agent_bridge import BaleAgentBridge


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


@dataclass(frozen=True)
class BaleHandlerDeps:
    bot: telebot.TeleBot
    logger: logging.Logger
    agent_bridge: BaleAgentBridge
    reply_long_text: Callable[[types.Message, str], None]
    payment_provider_token: str = ""
    api_url: str = "https://tapi.bale.ai/bot{0}/{1}"
