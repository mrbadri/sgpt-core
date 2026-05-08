"""Bale contact (phone) registration handler."""

from __future__ import annotations

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.handlers.deps import BaleHandlerDeps


def register_contact_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger

    @bot.message_handler(content_types=["contact"])
    def handle_contact(message: types.Message) -> None:
        reply = ""
        try:
            contact = message.contact
            if contact is None:
                bot.reply_to(message, "اطلاعات تماسی دریافت نشد. لطفاً دوباره تلاش کنید.")
                return

            phone_number = contact.phone_number or ""
            mobile = bale_user_service.normalize_mobile_from_contact(phone_number)
            if mobile is None:
                bot.reply_to(message, "شماره موبایل نامعتبر است. لطفاً دوباره تلاش کنید.")
                return

            bale_tid = message.from_user.id if message.from_user else None
            if bale_tid is None:
                bot.reply_to(message, "شناسه کاربر در دسترس نیست. لطفاً دوباره تلاش کنید.")
                return

            user_id_for_log = bale_tid

            try:
                db = get_db_session()
                try:
                    kind, user = bale_user_service.commit_user_for_bale_contact(
                        db, mobile, int(bale_tid)
                    )
                    if kind == "linked":
                        reply = f"✅ شماره {mobile} قبلاً ثبت شده است."
                        logger.info(
                            f"Contact already registered | user_id={user_id_for_log} mobile={mobile}"
                        )
                    else:
                        reply = f"✅ شماره {mobile} با موفقیت ثبت شد!"
                        logger.info(
                            f"User registered | user_id={user_id_for_log} "
                            f"mobile={mobile} db_id={user.id}"
                        )
                except Exception as db_err:
                    db.rollback()
                    reply = "متأسفانه در ثبت اطلاعات خطایی رخ داد. لطفاً دوباره تلاش کنید."
                    logger.error(f"Error saving user: {db_err}", exc_info=True)
                finally:
                    db.close()
            except Exception as session_err:
                reply = "متأسفانه در اتصال به پایگاه داده خطایی رخ داد."
                logger.error(f"Error creating DB session: {session_err}", exc_info=True)

            if reply:
                remove_keyboard = types.ReplyKeyboardRemove()
                bot.reply_to(message, reply, reply_markup=remove_keyboard)

        except Exception as e:
            logger.error(f"Error handling contact: {e}", exc_info=True)
            try:
                bot.reply_to(
                    message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
                )
            except Exception:
                pass
