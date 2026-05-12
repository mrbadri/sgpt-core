"""Plain text messages → deep agent for linked Bale users."""

from __future__ import annotations

import random
from typing import Union

from telebot import types

from app.agent.sample import StudentResponse
from app.db.session import get_db_session
from app.services import bale_user_service
from integrations.bale.formatting import markdown_to_bale_markdown, split_reply_text
from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming

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

# Maps bale_tid -> list of next_questions from the last structured response
_pending_questions: dict[str, list[str]] = {}


def _format_structured_response(resp: StudentResponse) -> str:
    """Convert a StudentResponse into a Bale-markdown formatted string."""
    lines: list[str] = []
    lines.append(f"*{resp.header}*")
    lines.append("")
    lines.append(resp.main_content)
    if resp.key_points:
        lines.append("")
        lines.append("📌 *نکات کلیدی:*")
        for point in resp.key_points:
            lines.append(f"• {point}")
    if resp.fun_fact:
        lines.append("")
        lines.append(f"💡 {resp.fun_fact}")
    return "\n".join(lines)


def _next_questions_keyboard(bale_tid: int, questions: list[str]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for i, q in enumerate(questions):
        markup.add(types.InlineKeyboardButton(q, callback_data=f"nq:{bale_tid}:{i}"))
    return markup


def register_deep_chat_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger
    bridge = deps.agent_bridge
    reply_long = deps.reply_long_text

    def _plain_text_predicate(m: types.Message) -> bool:
        txt = getattr(m, "text", None)
        return isinstance(txt, str) and bool(txt.strip()) and not txt.strip().startswith("/")

    def _send_answer(
        bale_tid: int,
        answer: Union[StudentResponse, str],
        reply_to: types.Message,
        status_msg: types.Message | None,
    ) -> None:
        """Render and send the agent answer, replacing the status message if present."""
        if isinstance(answer, StudentResponse):
            _pending_questions[str(bale_tid)] = list(answer.next_questions)
            body = _format_structured_response(answer)
            body_md = markdown_to_bale_markdown(body)
            markup = _next_questions_keyboard(bale_tid, answer.next_questions)

            if status_msg is not None:
                try:
                    bot.edit_message_text(
                        body_md,
                        chat_id=status_msg.chat.id,
                        message_id=status_msg.message_id,
                        parse_mode="Markdown",
                        reply_markup=markup,
                    )
                    return
                except Exception:
                    pass
            bot.send_message(reply_to.chat.id, body_md, parse_mode="Markdown", reply_markup=markup)
        else:
            # Plain-text fallback
            text_answer = answer if answer else (
                "🧐 عجب سوال چالشی‌ای! دقیقاً متوجه منظورت نشدم. یه جور دیگه بپرس یا جزئیات بیشتری بهم بده تا بترکونیم!"
            )
            answer_md = markdown_to_bale_markdown(text_answer)
            parts = split_reply_text(answer_md)
            if status_msg is not None and parts:
                first_chunk = parts[0] or " "
                try:
                    bot.edit_message_text(
                        first_chunk,
                        chat_id=status_msg.chat.id,
                        message_id=status_msg.message_id,
                        parse_mode="Markdown",
                    )
                except Exception:
                    reply_long(reply_to, answer_md)
                    return
                for chunk in parts[1:]:
                    bot.send_message(reply_to.chat.id, chunk or " ", parse_mode="Markdown")
            else:
                reply_long(reply_to, text_answer)

    @bot.message_handler(content_types=["text"], func=_plain_text_predicate)
    def handle_deep_chat(message: types.Message) -> None:
        uid = message.from_user.id if message.from_user else None
        raw = message.text.strip() if message.text else ""
        log_bale_incoming(
            "deep_chat text",
            chat_id=message.chat.id,
            user_id=uid,
            prompt_preview=raw[:120] if raw else "",
        )
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

            _send_answer(bale_tid, answer, message, status_msg[0])

        except Exception as e:
            logger.error(f"Error in handle_deep_chat: {e}", exc_info=True)
            try:
                bot.reply_to(
                    message,
                    "🎙️ یک-دو-سه، امتحان می‌کنیم! یه نویز کوچیک افتاد تو ارتباطمون. یه بار دیگه بفرست که پرقدرت بریم جلو! 💪",
                )
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("nq:"))
    def handle_next_question_callback(call: types.CallbackQuery) -> None:
        uid = call.from_user.id if call.from_user else None
        cid = call.message.chat.id if call.message else None
        log_bale_incoming(
            "callback next_question",
            chat_id=cid,
            user_id=uid,
            callback_data=call.data,
        )
        try:
            if not call.data:
                bot.answer_callback_query(call.id)
                return

            parts = call.data.split(":", 2)
            if len(parts) != 3:
                bot.answer_callback_query(call.id)
                return

            _, tid_str, idx_str = parts
            bale_tid = int(tid_str)
            idx = int(idx_str)

            questions = _pending_questions.get(str(bale_tid), [])
            if idx >= len(questions):
                bot.answer_callback_query(call.id, "سوال پیدا نشد!")
                return

            question = questions[idx]
            bot.answer_callback_query(call.id, "⏳ دارم جواب می‌دم...")

            if not call.message or not isinstance(call.message, types.Message):
                return

            origin_message: types.Message = call.message
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
                    status_msg[0] = bot.send_message(
                        origin_message.chat.id,
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
                    question,
                    on_thinking=on_thinking,
                    on_searching=on_searching,
                    on_got_it=on_got_it,
                )
            except Exception as agent_err:
                logger.error(f"Deep agent error (callback): {agent_err}", exc_info=True)
                msg = status_msg[0]
                if msg:
                    try:
                        bot.delete_message(msg.chat.id, msg.message_id)
                    except Exception:
                        pass
                bot.send_message(
                    origin_message.chat.id,
                    "⚡ انرژی سیستم یه لحظه افت کرد! دوباره بپرس تا با قدرت کامل جواب بدم. این دفعه حله! 🚀",
                )
                return

            _send_answer(bale_tid, answer, origin_message, status_msg[0])

        except Exception as e:
            logger.error(f"Error in handle_next_question_callback: {e}", exc_info=True)
            try:
                bot.answer_callback_query(call.id, "خطایی پیش آمد!")
            except Exception:
                pass
