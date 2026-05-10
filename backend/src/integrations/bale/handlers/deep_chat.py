"""Plain text messages → deep agent for linked Bale users."""

from __future__ import annotations

import random

from telebot import types

from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.formatting import markdown_to_bale_markdown, split_reply_text
from integrations.bale.handlers.deps import BaleHandlerDeps

_THINKING_STATUS_LINES: tuple[str, ...] = (
    "گرفتم! ⚡️ یه چند لحظه بهم زمان بده...",
    "حله! 🆗 الان بهت می‌گم چی به چیه...",
    "اوکی، بذار ببینم چطور می‌تونم کمکت کنم... 🤔",
    "شنیدم! 👂 دارم پاسخت رو ردیف می‌کنم...",
    "یک ثانیه صبر کن که دست پر بیام! 🚀",
    "پیامت رسید! 📩 دارم پردازشش می‌کنم...",
    "خیلی هم عالی! بذار یه تحلیل ریز بکنم... 🧐",
    "اوکی، یه لحظه دندون رو جگر بذار الان میام! ✨",
    "گرفتم چی شد! 🧠 ذهنم رو گذاشتم روش...",
    "خب، بذار ببینم چه جوری برات ردیفش می‌کنم... 🛠️",
)

_SEARCHING_STATUS_LINES: tuple[str, ...] = (
    "🔎 دارم یه بررسی سریع می‌کنم که دقیق‌ترین جواب رو بدم...",
    "📚 دارم لابه‌لای مطالب می‌گردم... الان پیداش می‌کنم!",
    "🔍 اجازه بده یه نگاهی به منابع بندازم، الان میام...",
    "🎯 دارم روی بهترین پاسخ تمرکز می‌کنم...",
    "📖 دارم مثل یه کارآگاه دنبال نکته‌های طلایی می‌گردم! 🕵️‍♂️",
    "🌐 دارم کل دیتابیس رو شخم می‌زنم برات...",
    "⚡️ یه لحظه صبر کن، دارم بهترین مسیر رو پیدا می‌کنم...",
    "🧩 دارم قطعات پازل رو کنار هم می‌چینم...",
    "🌀 دارم از میون هزارتا مطلب، اصل جنس رو برات سوا می‌کنم!",
    "⏳ یه ذره دیگه تحمل کن، دارم به جاهای خوبش می‌رسم...",
)

_GOT_IT_STATUS_LINES: tuple[str, ...] = (
    "💡 آها! یافتم! بذار مرتبش کنم که برات بفرستم...",
    "✅ اوکی، آماده شد! الان می‌فرستمش...",
    "✨ خیل خب، اینم از این! ببین چطوره...",
    "🎉 تمام! دارم متن نهایی رو برات ردیف می‌کنم...",
    "💎 آها! یه چیز خیلی مشتی پیدا کردم، الان می‌بینی...",
    "📝 دارم دسته‌بندی‌ش می‌کنم که هلو بره تو گلو! 🍑",
    "🚀 موتورم گرم شد! بیا که جواب حاضره...",
    "🔥 حله، جواب دقیقاً همینه که الان می‌فرستم...",
    "👌 یافتم! دارم آخرین ویرایش‌ها رو انجام می‌دم...",
    "🎈 تمومه! برو بریم برای دیدن جواب...",
)


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
        print("deep chat command received =======================================")
        try:
            if not message.from_user:
                bot.reply_to(
                    message,
                    "🧐 اوه! سیستم یه لحظه گیج شد و نشناختت. یه بار دیگه پیام بده تا ارتباطمون وصل شه.",
                )
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
                    "🧠 دارم حافظه‌م رو برای جواب دادن بهت ریکاوری می‌کنم... چند لحظه دیگه دوباره بپرس، الان اوکی می‌شم! ✨",
                )
                return

            if linked is None:
                bot.reply_to(
                    message,
                    "👋 هنوز با هم رفیق نشدیم که! اول دکمه /start رو بزن و «ارسال شماره من» رو انتخاب کن تا بتونم توی درس‌ها کمکت کنم. منتظرتم! 💬",
                )
                return

            # Mutable container so nested closures can reassign the reference.
            status_msg: list[types.Message | None] = [None]

            def _edit_status(text: str) -> None:
                msg = status_msg[0]
                if msg is None:
                    return
                try:
                    bot.edit_message_text(text, chat_id=msg.chat.id, message_id=msg.message_id)
                except Exception:
                    pass

            def on_thinking() -> None:
                try:
                    status_msg[0] = bot.reply_to(
                        message,
                        random.choice(_THINKING_STATUS_LINES),
                    )
                except Exception:
                    pass

            def on_searching() -> None:
                _edit_status(random.choice(_SEARCHING_STATUS_LINES))

            def on_got_it() -> None:
                _edit_status(random.choice(_GOT_IT_STATUS_LINES))

            try:
                answer = bridge.invoke_reply_with_status(
                    bale_tid,
                    prompt,
                    on_thinking=on_thinking,
                    on_searching=on_searching,
                    on_got_it=on_got_it,
                )
            except Exception as agent_err:
                logger.error(f"Deep agent error: {agent_err}", exc_info=True)
                msg = status_msg[0]
                if msg:
                    try:
                        bot.delete_message(msg.chat.id, msg.message_id)
                    except Exception:
                        pass
                bot.reply_to(
                    message,
                    "⚡ انرژی سیستم یه لحظه افت کرد! دوباره بپرس تا با قدرت کامل جواب بدم. این دفعه حله! 🚀",
                )
                return

            if not answer:
                answer = (
                    "🧐 عجب سوال چالشی‌ای! دقیقاً متوجه منظورت نشدم. یه جور دیگه بپرس یا جزئیات بیشتری بهم بده تا بترکونیم!"
                )

            answer_md = markdown_to_bale_markdown(answer)
            parts = split_reply_text(answer_md)
            status = status_msg[0]
            if status is not None and parts:
                first_chunk = parts[0] or " "
                try:
                    bot.edit_message_text(
                        first_chunk,
                        chat_id=status.chat.id,
                        message_id=status.message_id,
                        parse_mode="Markdown",
                    )
                except Exception:
                    reply_long(message, answer_md)
                else:
                    for chunk in parts[1:]:
                        bot.send_message(message.chat.id, chunk or " ", parse_mode="Markdown")
            else:
                reply_long(message, answer)

        except Exception as e:
            logger.error(f"Error in handle_deep_chat: {e}", exc_info=True)
            try:
                bot.reply_to(
                    message,
                    "🎙️ یک-دو-سه، امتحان می‌کنیم! یه نویز کوچیک افتاد تو ارتباطمون. یه بار دیگه بفرست که پرقدرت بریم جلو! 💪",
                )
            except Exception:
                pass