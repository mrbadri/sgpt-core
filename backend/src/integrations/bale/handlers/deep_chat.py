"""Plain text messages → deep agent for linked Bale users."""

from __future__ import annotations

import random
from typing import Union

from telebot import types

from app.agent.format_response import AgentResponse
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
# Maps bale_tid -> list of ExamQuestion for the active exam
_pending_exams: dict[str, list] = {}


def _format_main_response(resp: AgentResponse) -> str:
    """Render the main body of an AgentResponse (no header, no exam questions)."""
    lines: list[str] = [resp.main_content]

    if resp.response_type == "teaching":
        if resp.key_points:
            lines += ["", "📌 *نکات کلیدی:*"]
            lines += [f"• {p}" for p in resp.key_points]
        if resp.fun_fact:
            lines += ["", f"💡 {resp.fun_fact}"]

    elif resp.response_type == "welcome":
        if resp.fun_fact:
            lines += ["", f"🔍 *تحلیل شخصیت:* {resp.fun_fact}"]

    # exam / simple: main_content only here; questions sent separately

    return "\n".join(lines)


def _next_questions_keyboard(bale_tid: int, questions: list[str]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for i, q in enumerate(questions):
        markup.add(types.InlineKeyboardButton(q, callback_data=f"nq:{bale_tid}:{i}"))
    return markup


def _exam_question_keyboard(bale_tid: int, q_idx: int, options: list[str]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for opt_idx, opt in enumerate(options):
        markup.add(types.InlineKeyboardButton(opt, callback_data=f"eq:{bale_tid}:{q_idx}:{opt_idx}"))
    return markup


# Keep old name as alias so welcome.py import still works
_format_structured_response = _format_main_response


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
        answer: Union[AgentResponse, str],
        reply_to: types.Message,
        status_msg: types.Message | None,
    ) -> None:
        """Render and send the agent answer, replacing the status message if present."""
        if isinstance(answer, AgentResponse):
            body_md = markdown_to_bale_markdown(_format_main_response(answer))

            if answer.response_type == "exam":
                # Main content replaces the status message (no next-question keyboard)
                if status_msg is not None:
                    try:
                        bot.edit_message_text(
                            body_md,
                            chat_id=status_msg.chat.id,
                            message_id=status_msg.message_id,
                            parse_mode="Markdown",
                        )
                    except Exception:
                        bot.send_message(reply_to.chat.id, body_md, parse_mode="Markdown")
                else:
                    bot.send_message(reply_to.chat.id, body_md, parse_mode="Markdown")

                # Send each question as a separate message with option buttons
                if answer.exam_questions:
                    _pending_exams[str(bale_tid)] = list(answer.exam_questions)
                    for q_idx, q in enumerate(answer.exam_questions):
                        markup = _exam_question_keyboard(bale_tid, q_idx, q.options)
                        bot.send_message(
                            reply_to.chat.id,
                            f"*سوال {q_idx + 1}:* {q.question}",
                            parse_mode="Markdown",
                            reply_markup=markup,
                        )
            else:
                questions = list(answer.next_questions) if answer.next_questions else []
                _pending_questions[str(bale_tid)] = questions
                markup = _next_questions_keyboard(bale_tid, questions) if questions else None

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
            bot.answer_callback_query(call.id)

            if not call.message or not isinstance(call.message, types.Message):
                return

            chat_id = call.message.chat.id

            # Show the question as a standalone message (simulates user typing it)
            try:
                question_msg = bot.send_message(chat_id, f"❓ {question}")
            except Exception:
                question_msg = call.message

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
                        question_msg,
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
                    chat_id,
                    "⚡ انرژی سیستم یه لحظه افت کرد! دوباره بپرس تا با قدرت کامل جواب بدم. این دفعه حله! 🚀",
                )
                return

            _send_answer(bale_tid, answer, question_msg, status_msg[0])

        except Exception as e:
            logger.error(f"Error in handle_next_question_callback: {e}", exc_info=True)
            try:
                bot.answer_callback_query(call.id, "خطایی پیش آمد!")
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("eq:"))
    def handle_exam_answer_callback(call: types.CallbackQuery) -> None:
        try:
            if not call.data:
                bot.answer_callback_query(call.id)
                return

            parts = call.data.split(":", 3)
            if len(parts) != 4:
                bot.answer_callback_query(call.id)
                return

            _, tid_str, q_idx_str, opt_idx_str = parts
            bale_tid = int(tid_str)
            q_idx = int(q_idx_str)
            opt_idx = int(opt_idx_str)

            exam_qs = _pending_exams.get(str(bale_tid), [])
            if q_idx >= len(exam_qs):
                bot.answer_callback_query(call.id, "سوال پیدا نشد!")
                return

            q = exam_qs[q_idx]
            if opt_idx >= len(q.options):
                bot.answer_callback_query(call.id, "گزینه نامعتبر!")
                return

            chosen = q.options[opt_idx]
            is_correct = chosen.strip() == q.correct_answer.strip()

            if is_correct:
                bot.answer_callback_query(call.id, "✅ آفرین! پاسخ درسته!")
                result_text = f"✅ *پاسخ درست!* _{chosen}_"
            else:
                bot.answer_callback_query(call.id, "❌ اشتباه بود!")
                result_text = (
                    f"❌ *اشتباه!* گزینه انتخابی: _{chosen}_\n"
                    f"✅ *پاسخ صحیح:* _{q.correct_answer}_"
                )

            if not call.message or not isinstance(call.message, types.Message):
                return

            chat_id = call.message.chat.id

            # Show feedback + single "explain" button (no agent call yet)
            explain_markup = types.InlineKeyboardMarkup()
            explain_markup.add(types.InlineKeyboardButton(
                "💡 توضیح بیشتر می‌خوام",
                callback_data=f"ex:{bale_tid}:{q_idx}",
            ))
            try:
                bot.edit_message_text(
                    f"*سوال {q_idx + 1}:* {q.question}\n\n{result_text}",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=explain_markup,
                )
            except Exception:
                bot.send_message(chat_id, result_text, parse_mode="Markdown")

            # Silently record this answer so the agent knows about it on the next call
            result_label = "درست" if is_correct else "اشتباه"
            bridge.add_exam_context(
                bale_tid,
                f"سوال {q_idx + 1}: {q.question} | انتخابی: {chosen} | صحیح: {q.correct_answer} | {result_label}",
            )

        except Exception as e:
            logger.error(f"Error in handle_exam_answer_callback: {e}", exc_info=True)
            try:
                bot.answer_callback_query(call.id, "خطایی پیش آمد!")
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("ex:"))
    def handle_exam_explain_callback(call: types.CallbackQuery) -> None:
        try:
            if not call.data:
                bot.answer_callback_query(call.id)
                return

            parts = call.data.split(":", 2)
            if len(parts) != 3:
                bot.answer_callback_query(call.id)
                return

            _, tid_str, q_idx_str = parts
            bale_tid = int(tid_str)
            q_idx = int(q_idx_str)

            exam_qs = _pending_exams.get(str(bale_tid), [])
            if q_idx >= len(exam_qs):
                bot.answer_callback_query(call.id, "سوال پیدا نشد!")
                return

            q = exam_qs[q_idx]
            bot.answer_callback_query(call.id, "⏳ دارم توضیح می‌دم...")

            if not call.message or not isinstance(call.message, types.Message):
                return

            chat_id = call.message.chat.id

            # Remove the explain button from the question message
            try:
                bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=types.InlineKeyboardMarkup(),
                )
            except Exception:
                pass

            # Show the question as a standalone message, then reply to it
            try:
                question_msg = bot.send_message(chat_id, f"❓ {q.question}")
            except Exception:
                question_msg = call.message

            explanation_prompt = (
                f"لطفاً این سوال آزمون را کامل توضیح بده:\n"
                f"سوال: {q.question}\n"
                f"گزینه‌ها: {', '.join(q.options)}\n"
                f"پاسخ صحیح: {q.correct_answer}\n"
                f"چرا پاسخ صحیح درست است و چرا بقیه گزینه‌ها اشتباه هستند؟"
            )

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
                    status_msg[0] = bot.reply_to(question_msg, random.choice(_THINKING_STATUS_LINES))
                except Exception:
                    pass

            def on_searching() -> None:
                _edit_status(random.choice(_SEARCHING_STATUS_LINES))

            def on_got_it() -> None:
                _edit_status(random.choice(_GOT_IT_STATUS_LINES))

            try:
                answer = bridge.invoke_reply_with_status(
                    bale_tid,
                    explanation_prompt,
                    on_thinking=on_thinking,
                    on_searching=on_searching,
                    on_got_it=on_got_it,
                )
            except Exception as agent_err:
                logger.error(f"Exam explain agent error: {agent_err}", exc_info=True)
                msg = status_msg[0]
                if msg:
                    try:
                        bot.delete_message(msg.chat.id, msg.message_id)
                    except Exception:
                        pass
                bot.send_message(chat_id, "⚡ خطایی پیش آمد، دوباره تلاش کن.")
                return

            _send_answer(bale_tid, answer, question_msg, status_msg[0])

        except Exception as e:
            logger.error(f"Error in handle_exam_explain_callback: {e}", exc_info=True)
            try:
                bot.answer_callback_query(call.id, "خطایی پیش آمد!")
            except Exception:
                pass
