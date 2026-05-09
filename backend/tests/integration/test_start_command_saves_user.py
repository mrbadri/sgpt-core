"""Tests for Bale bot handlers (start, contact, deep chat)."""

from unittest.mock import Mock, patch

from telebot import types
from sqlmodel import select

from app.models.user import User
from app.services.agent_bridge import BaleAgentBridge
from integrations.bale.bot_service import BotService


def _handler_for_commands(bot_service: BotService, commands: list[str]):
    for registered in bot_service.bot.message_handlers:
        if registered["filters"].get("commands") == commands:
            return registered["function"]
    return None


def _handler_for_content_types(bot_service: BotService, content_types: list[str]):
    for registered in bot_service.bot.message_handlers:
        if registered["filters"].get("content_types") == content_types:
            return registered["function"]
    return None


def _text_handler(bot_service: BotService):
    for registered in bot_service.bot.message_handlers:
        filt = registered["filters"]
        if filt.get("content_types") == ["text"] and filt.get("func") is not None:
            return registered["function"]
    return None


class TestStartCommand:
    """Registration prompt only; persistence happens on contact."""

    def test_start_replies_with_registration_prompt(self):
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        bot_service.bot.reply_to = Mock()

        message = Mock(spec=types.Message)
        message.text = "/start"
        message.chat = Mock()
        message.chat.id = 12345
        message.from_user = Mock()
        message.from_user.id = 67890

        handler = _handler_for_commands(bot_service, ["start"])
        assert handler is not None
        handler(message)

        bot_service.bot.reply_to.assert_called_once()
        reply_text = bot_service.bot.reply_to.call_args[0][1]
        assert "ثبت‌نام" in reply_text
        assert bot_service.bot.reply_to.call_args[1]["reply_markup"] is not None


class TestContactHandler:
    @patch("integrations.bale.handlers.contact.get_db_session")
    def test_contact_creates_user(self, mock_get_db, test_db):
        mock_get_db.return_value = test_db

        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        bot_service.bot.reply_to = Mock()

        message = Mock(spec=types.Message)
        message.contact = Mock()
        message.contact.phone_number = "+989123456789"
        message.from_user = Mock()
        message.from_user.id = 42
        message.chat = Mock()
        message.chat.id = 1

        handler = _handler_for_content_types(bot_service, ["contact"])
        assert handler is not None
        handler(message)

        stored = test_db.exec(select(User).where(User.mobile == 9123456789)).first()
        assert stored is not None
        assert stored.bale_user_id == 42
        bot_service.bot.reply_to.assert_called()

    @patch("integrations.bale.handlers.contact.get_db_session")
    def test_contact_links_existing_mobile(self, mock_get_db, test_db):
        mock_get_db.return_value = test_db
        user = User(mobile=9120000000, bale_user_id=None)
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        bot_service.bot.reply_to = Mock()

        message = Mock(spec=types.Message)
        message.contact = Mock()
        message.contact.phone_number = "09120000000"
        message.from_user = Mock()
        message.from_user.id = 99
        message.chat = Mock()
        message.chat.id = 1

        handler = _handler_for_content_types(bot_service, ["contact"])
        assert handler is not None
        handler(message)

        row = test_db.exec(select(User).where(User.mobile == 9120000000)).first()
        assert row is not None
        assert row.bale_user_id == 99


class TestDeepChatHandler:
    @patch.object(BaleAgentBridge, "invoke_reply", return_value="سلام از دستیار")
    @patch("integrations.bale.handlers.deep_chat.get_db_session")
    def test_plain_text_uses_agent_when_linked(self, mock_get_db, _mock_invoke, test_db):
        mock_get_db.return_value = test_db
        user = User(mobile=9130000000, bale_user_id=7001)
        test_db.add(user)
        test_db.commit()

        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        bot_service.bot.reply_to = Mock()
        bot_service.bot.send_message = Mock()

        message = Mock(spec=types.Message)
        message.text = "hello assistant"
        message.from_user = Mock()
        message.from_user.id = 7001
        message.chat = Mock()
        message.chat.id = 55

        handler = _text_handler(bot_service)
        assert handler is not None
        handler(message)

        bot_service.bot.reply_to.assert_called()
        call_text = bot_service.bot.reply_to.call_args[0][1]
        assert "سلام از دستیار" in call_text
