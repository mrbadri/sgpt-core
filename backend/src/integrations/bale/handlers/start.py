"""Bale /start command handler."""

from __future__ import annotations

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming
from integrations.bale.handlers.welcome import run_welcome_step


def register_start_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger
    bridge = deps.agent_bridge

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
            linked_user = None
            if uid:
                try:
                    db = get_db_session()
                    try:
                        linked_user = bale_user_service.fetch_user_by_identity(db, "bale", str(uid))
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"DB error in start handler: {db_err}", exc_info=True)

            if uid:
                user_id = linked_user.id if linked_user else None
                deps.log_message(user_id, "bale", "in", "command", "/start", message.message_id)

            if linked_user:
                run_welcome_step(bot, message, logger, bridge, linked_user.id)
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
            deps.log_message(None, "bale", "out", "text", greeting)

            logger.info(f"/start received | user_id={uid} chat_id={message.chat.id}")

        except Exception as e:
            logger.error(f"Error handling start command: {e}", exc_info=True)
            try:
                bot.reply_to(message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except Exception:
                pass
