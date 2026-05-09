"""Bale /start command handler."""

from __future__ import annotations

from telebot import types

from integrations.bale.handlers.deps import BaleHandlerDeps


def register_start_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger

    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message) -> None:
        print("start command received =======================================")
        try:
            user_id = message.from_user.id if message.from_user else None
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
                f"/start received | user_id={user_id} "
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
