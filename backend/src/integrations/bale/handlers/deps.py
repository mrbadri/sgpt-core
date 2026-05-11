"""Dependency bundle for Bale message handlers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

import telebot
from telebot import types

from app.services.agent_bridge import BaleAgentBridge


@dataclass(frozen=True)
class BaleHandlerDeps:
    bot: telebot.TeleBot
    logger: logging.Logger
    agent_bridge: BaleAgentBridge
    reply_long_text: Callable[[types.Message, str], None]
    payment_provider_token: str = ""
    api_url: str = "https://tapi.bale.ai/bot{0}/{1}"
