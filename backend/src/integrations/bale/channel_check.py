"""Bale channel membership check and related helpers."""

from __future__ import annotations

import logging

from telebot import TeleBot, types

from app.settings import settings

_MEMBER_STATUSES = {"member", "administrator", "creator"}


def check_channel_membership(bot: TeleBot, user_id: int) -> list[str]:
    """Return channels from settings that the user has NOT joined."""
    missing: list[str] = []
    for channel in settings.bale_required_channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            print("===============================")
            print("=====>===>member:", member)
            print("===============================")
            if member.status not in _MEMBER_STATUSES:
                missing.append(channel)
        except Exception as e:
            err = str(e)
            if "403" in err or "permission_denied" in err:
                # Bot is not an admin of the channel — cannot verify membership.
                # Add the bot as a channel administrator to resolve this.
                logging.getLogger(__name__).warning(
                    f"Bot lacks admin access to {channel}; skipping membership check"
                )
            else:
                print("Error ===========------0-------->" , e)
                missing.append(channel)
    return missing


def run_channel_check(bot: TeleBot, message: types.Message, logger: logging.Logger) -> None:
    """Check channel membership and reply with prompt or welcome."""
    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        return

    missing = check_channel_membership(bot, user_id)

    if missing:
        lines = "\n".join(f"• {ch}" for ch in missing)
        keyboard = types.InlineKeyboardMarkup()
        for ch in missing:
            url = f"https://ble.ir/{ch.lstrip('@')}" if ch.startswith("@") else ch
            keyboard.add(types.InlineKeyboardButton(text=f"عضویت در {ch}", url=url))
        bot.reply_to(
            message,
            f"برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:\n{lines}",
            reply_markup=keyboard,
        )
        logger.info(f"Channel check failed | user_id={user_id} missing={missing}")
    else:
        remove_keyboard = types.ReplyKeyboardRemove()
        bot.reply_to(
            message,
            "✅ ثبت‌نام شما کامل شد! اکنون می‌توانید از ربات استفاده کنید.",
            reply_markup=remove_keyboard,
        )
        logger.info(f"Channel check passed | user_id={user_id}")
