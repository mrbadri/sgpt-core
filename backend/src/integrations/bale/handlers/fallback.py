"""Catch-all handler (e.g. unknown slash commands)."""

from __future__ import annotations

from telebot import types

from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming


def register_fallback_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger

    @bot.message_handler(func=lambda m: True)
    def handle_unknown(message: types.Message) -> None:
        try:
            if message.text and message.text.startswith("/"):
                uid = message.from_user.id if message.from_user else None
                log_bale_incoming(
                    "unknown command (fallback)",
                    chat_id=message.chat.id,
                    user_id=uid,
                    text=message.text,
                )
                logger.warning(
                    f"Unknown command received from user {message.from_user}: {message.text}"
                )
        except Exception as e:
            logger.error(f"Error handling unknown command: {e}", exc_info=True)
