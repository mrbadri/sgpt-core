"""Send potentially long replies as multiple Bale/Telegram messages."""

from __future__ import annotations

import telebot
from telebot import types

from integrations.bale.formatting import markdown_to_bale_markdown, split_reply_text


def reply_long_text(bot: telebot.TeleBot, message: types.Message, text: str) -> None:
    html = markdown_to_bale_markdown(text)
    parts = split_reply_text(html)
    for idx, chunk in enumerate(parts):
        if idx == 0:
            bot.reply_to(message, chunk or " ", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, chunk or " ", parse_mode="Markdown")
