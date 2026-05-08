"""Plain text messages → deep agent for linked Bale users."""

from __future__ import annotations

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.handlers.deps import BaleHandlerDeps


def register_deep_chat_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger
    bridge = deps.agent_bridge
    reply_long = deps.reply_long_text

    def _plain_text_predicate(m: types.Message) -> bool:
        txt = getattr(m, "text", None)
        return isinstance(txt, str) and bool(txt.strip()) and not txt.strip().startswith("/")

    @bot.message_handler(content_types=["text"], func=_plain_text_predicate)
    def handle_deep_chat(message: types.Message) -> None:
        try:
            if not message.from_user:
                bot.reply_to(message, "شناسه کاربر در دسترس نیست.")
                return

            bale_tid = int(message.from_user.id)
            prompt = message.text.strip() if message.text else ""

            try:
                db = get_db_session()
                try:
                    linked = bale_user_service.fetch_user_by_bale_user_id(db, bale_tid)
                finally:
                    db.close()
            except Exception as session_err:
                logger.error(f"Deep chat DB lookup failed: {session_err}", exc_info=True)
                bot.reply_to(
                    message,
                    "متأسفانه در اتصال به پایگاه داده خطایی رخ داد. بعداً امتحان کنید.",
                )
                return

            if linked is None:
                bot.reply_to(
                    message,
                    "برای استفاده از دستیار، ابتدا /start را بزنید و شمارهٔ خود را با دکمه «ارسال شماره من» بفرستید.",
                )
                return

            try:
                answer = bridge.invoke_reply(bale_tid, prompt)
            except Exception as agent_err:
                logger.error(f"Deep agent error: {agent_err}", exc_info=True)
                bot.reply_to(
                    message,
                    "در حال حاضر نتوانستم پاسخ بدهم. لطفاً بعداً دوباره تلاش کنید.",
                )
                return

            if not answer:
                answer = "پاسخی ندارم."

            reply_long(message, answer)

        except Exception as e:
            logger.error(f"Error in handle_deep_chat: {e}", exc_info=True)
            try:
                bot.reply_to(
                    message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
                )
            except Exception:
                pass
