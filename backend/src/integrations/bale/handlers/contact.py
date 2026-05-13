"""Bale contact (phone) registration handler."""

from __future__ import annotations

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming
from integrations.bale.handlers.welcome import run_welcome_step


def register_contact_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger
    bridge = deps.agent_bridge

    @bot.message_handler(content_types=["contact"])
    def handle_contact(message: types.Message) -> None:
        try:
            contact = message.contact
            if contact is None:
                bot.reply_to(message, "اطلاعات تماسی دریافت نشد. لطفاً دوباره تلاش کنید.")
                return

            uid = message.from_user.id if message.from_user else None
            pn = contact.phone_number or ""
            phone_hint = f"***{pn[-4:]}" if len(pn) >= 4 else "(short)"
            log_bale_incoming(
                "message contact",
                chat_id=message.chat.id,
                user_id=uid,
                phone_hint=phone_hint,
                message_id=message.message_id,
            )

            mobile = bale_user_service.normalize_mobile_from_contact(pn)
            if mobile is None:
                bot.reply_to(message, "شماره موبایل نامعتبر است. لطفاً دوباره تلاش کنید.")
                return

            bale_tid = uid
            if bale_tid is None:
                bot.reply_to(message, "شناسه کاربر در دسترس نیست. لطفاً دوباره تلاش کنید.")
                return

            db_error: str | None = None
            try:
                db = get_db_session()
                try:
                    kind, user = bale_user_service.commit_user_for_bale_contact(
                        db, mobile, int(bale_tid)
                    )
                    logger.info(
                        f"Contact {kind} | user_id={bale_tid} mobile={mobile} db_id={user.id}"
                    )
                except Exception as db_err:
                    db.rollback()
                    db_error = "متأسفانه در ثبت اطلاعات خطایی رخ داد. لطفاً دوباره تلاش کنید."
                    logger.error(f"Error saving user: {db_err}", exc_info=True)
                finally:
                    db.close()
            except Exception as session_err:
                db_error = "متأسفانه در اتصال به پایگاه داده خطایی رخ داد."
                logger.error(f"Error creating DB session: {session_err}", exc_info=True)

            if db_error:
                bot.reply_to(message, db_error)
                return

            run_welcome_step(bot, message, logger, bridge)

        except Exception as e:
            logger.error(f"Error handling contact: {e}", exc_info=True)
            try:
                bot.reply_to(message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except Exception:
                pass
