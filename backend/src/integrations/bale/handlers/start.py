"""Bale /start command handler."""

from __future__ import annotations

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from app.settings import settings
from integrations.bale.channel_check import run_channel_check
from integrations.bale.get_profile import get_bale_profile_photo_url
from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming


def register_start_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger

    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message) -> None:
        uid = message.from_user.id if message.from_user else None
        uname = message.from_user.username if message.from_user else None
        log_bale_incoming(
            "command /start",
            chat_id=message.chat.id,
            user_id=uid,
            username=uname,
            text=getattr(message, "text", None),
        )
        try:
            if uid and settings.bale_bot_token:
                profile_url = get_bale_profile_photo_url(settings.bale_bot_token, uid)
                print("==============================================")
                print("======> profile_url:", profile_url)
                print("==============================================")

            # Check if user is already linked
            linked_user = None
            if uid:
                try:
                    db = get_db_session()
                    try:
                        linked_user = bale_user_service.fetch_user_by_bale_user_id(db, uid)
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"DB error in start handler: {db_err}", exc_info=True)

            if linked_user:
                run_channel_check(bot, message, logger)
                return

            # Not linked → ask for contact
            greeting = "سلام! برای ثبت‌نام، لطفاً دکمه «ارسال شماره من» را لمس کنید 📲"
            contact_button = types.KeyboardButton(
                text="📱 ارسال شماره من",
                request_contact=True,
            )
            keyboard = types.ReplyKeyboardMarkup(
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            keyboard.add(contact_button)
            bot.reply_to(message, greeting, reply_markup=keyboard)

            logger.info(
                f"/start received | user_id={uid} "
                f"chat_id={message.chat.id}"
            )

        except Exception as e:
            logger.error(f"Error handling start command: {e}", exc_info=True)
            try:
                bot.reply_to(
                    message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
                )
            except Exception:
                pass
