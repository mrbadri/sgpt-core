"""Send potentially long replies as multiple Bale/Telegram messages."""

from __future__ import annotations

import telebot
from telebot import types

from integrations.bale.formatting import split_reply_text


def reply_long_text(bot: telebot.TeleBot, message: types.Message, text: str) -> None:
    parts = split_reply_text(text)
    for idx, chunk in enumerate(parts):
        if idx == 0:
            bot.reply_to(message, chunk or " ")
        else:
            bot.send_message(message.chat.id, chunk or " ")
