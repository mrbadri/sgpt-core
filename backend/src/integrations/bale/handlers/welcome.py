"""Welcome step: profile analysis, agent greeting, and long-term memory init."""

from __future__ import annotations

import logging

from telebot import TeleBot, types

from app.agent.format_response import AgentResponse
from app.services.agent_bridge import BaleAgentBridge
from app.settings import settings
from integrations.bale.formatting import markdown_to_bale_markdown
from integrations.bale.get_profile import get_bale_profile_photo_url
from integrations.bale.handlers.deep_chat import (
    _format_structured_response,
    _next_questions_keyboard,
    _pending_questions,
)


def run_welcome_step(
    bot: TeleBot,
    message: types.Message,
    logger: logging.Logger,
    bridge: BaleAgentBridge,
) -> None:
    """Fetch profile photo, run onboarding agent, display full response, save memory."""
    uid = message.from_user.id if message.from_user else None
    if uid is None:
        return

    first_name = (message.from_user.first_name or "") if message.from_user else ""

    try:
        profile_url: str | None = None
        if settings.bale_bot_token:
            profile_url = get_bale_profile_photo_url(settings.bale_bot_token, uid)

        result = bridge.invoke_welcome(uid, first_name, profile_url)

        remove_kb = types.ReplyKeyboardRemove()

        if isinstance(result, AgentResponse):
            # Save fun_fact (personality analysis) to long-term memory
            bridge.save_user_memory(uid, first_name, result.fun_fact or "")

            # Format and send exactly like deep_chat does (personality visible via 💡 fun_fact)
            questions = list(result.next_questions) if result.next_questions else []
            _pending_questions[str(uid)] = questions
            body = _format_structured_response(result)
            body_md = markdown_to_bale_markdown(body)
            markup = _next_questions_keyboard(uid, questions) if questions else None

            # First message removes the contact keyboard, shows the greeting + personality
            bot.reply_to(message, body_md, reply_markup=remove_kb, parse_mode="Markdown")
            # Second message attaches the inline suggested-questions keyboard
            if questions:
                bot.send_message(
                    message.chat.id,
                    "💬 سوال‌های پیشنهادی:",
                    reply_markup=markup,
                )
        else:
            bridge.save_user_memory(uid, first_name, "")
            greeting = result or f"سلام {first_name}! به SGPT 1 خوش اومدی 🎉"
            bot.reply_to(message, greeting, reply_markup=remove_kb)

        logger.info(f"Welcome step complete | user_id={uid}")

    except Exception as e:
        logger.error(f"Welcome step error | user_id={uid}: {e}", exc_info=True)
        try:
            bot.reply_to(
                message,
                "✅ ثبت‌نام شما کامل شد! برای شروع، سوال خود را بپرسید.",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        except Exception:
            pass
