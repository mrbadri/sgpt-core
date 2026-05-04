"""Integration tests for /start command saving user."""

from unittest.mock import Mock, patch, MagicMock
import pytest
from telebot import types

from features.users.models import BotUser
from features.users.repository import BotUserRepository
from features.users.schemas import BotUserCreate
from integrations.bale.bot_service import BotService


class TestStartCommandSavesUser:
    """Test suite for /start command user saving integration."""

    @patch('integrations.bale.bot_service.get_db_session')
    def test_start_command_saves_new_user(self, mock_get_db_session, test_db):
        """Test /start command saves new user to database."""
        # Arrange
        mock_get_db_session.return_value = test_db
        
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        
        message = Mock(spec=types.Message)
        message.text = "/start"
        message.chat = Mock()
        message.chat.id = 12345
        from_user = Mock()
        from_user.id = 67890
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user
        
        # Mock bot.reply_to to avoid actual API call
        bot_service.bot.reply_to = Mock()

        # Act
        # Simulate the handler being called
        handler = None
        for registered_handler in bot_service.bot.message_handlers:
            if registered_handler['filters']['commands'] == ['start']:
                handler = registered_handler['function']
                break
        
        assert handler is not None, "Start command handler not found"
        handler(message)

        # Assert
        # Verify user was saved to database
        repository = BotUserRepository(test_db)
        saved_user = repository.get_by_bale_user_id(67890)
        
        assert saved_user is not None
        assert saved_user.bale_user_id == 67890
        assert saved_user.username == "testuser"
        assert saved_user.first_name == "Test"
        assert saved_user.last_name == "User"
        assert saved_user.is_bot is False
        assert saved_user.language_code == "en"
        
        # Verify bot replied
        bot_service.bot.reply_to.assert_called_once()
        
        # Verify database session was created
        mock_get_db_session.assert_called()

    @patch('integrations.bale.bot_service.get_db_session')
    def test_start_command_idempotent_existing_user(self, mock_get_db_session, test_db):
        """Test /start command is idempotent - doesn't create duplicate users."""
        # Arrange
        mock_get_db_session.return_value = test_db
        
        # Create user first
        repository = BotUserRepository(test_db)
        user_data = {
            'bale_user_id': 67890,
            'username': 'existinguser',
            'first_name': 'Existing',
            'last_name': 'User',
            'is_bot': False,
            'language_code': 'en',
        }
        repository.create(BotUserCreate(**user_data))
        
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        
        message = Mock(spec=types.Message)
        message.text = "/start"
        message.chat = Mock()
        message.chat.id = 12345
        from_user = Mock()
        from_user.id = 67890  # Same user ID
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user
        
        bot_service.bot.reply_to = Mock()

        # Act
        handler = None
        for registered_handler in bot_service.bot.message_handlers:
            if registered_handler['filters']['commands'] == ['start']:
                handler = registered_handler['function']
                break
        
        assert handler is not None
        handler(message)

        # Assert
        # Verify only one user exists with this bale_user_id
        all_users = test_db.query(BotUser).filter(BotUser.bale_user_id == 67890).all()
        assert len(all_users) == 1
        
        # Verify bot replied (command should succeed even if user exists)
        bot_service.bot.reply_to.assert_called_once()

    @patch('integrations.bale.bot_service.get_db_session')
    def test_start_command_with_payload(self, mock_get_db_session, test_db):
        """Test /start command with payload saves user and includes payload in response."""
        # Arrange
        mock_get_db_session.return_value = test_db
        
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        
        message = Mock(spec=types.Message)
        message.text = "/start invite_token_123"
        message.chat = Mock()
        message.chat.id = 12345
        from_user = Mock()
        from_user.id = 67890
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user
        
        bot_service.bot.reply_to = Mock()

        # Act
        handler = None
        for registered_handler in bot_service.bot.message_handlers:
            if registered_handler['filters']['commands'] == ['start']:
                handler = registered_handler['function']
                break
        
        assert handler is not None
        handler(message)

        # Assert
        # Verify user was saved
        repository = BotUserRepository(test_db)
        saved_user = repository.get_by_bale_user_id(67890)
        assert saved_user is not None
        
        # Verify bot replied with payload in message
        bot_service.bot.reply_to.assert_called_once()
        call_args = bot_service.bot.reply_to.call_args
        reply_message = call_args[0][1]  # Second argument is the reply text
        assert "invite_token_123" in reply_message

    @patch('integrations.bale.bot_service.get_db_session')
    def test_start_command_handles_database_error_gracefully(self, mock_get_db_session, test_db):
        """Test /start command handles database errors gracefully."""
        # Arrange
        # Simulate database error
        mock_get_db_session.side_effect = Exception("Database connection failed")
        
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        
        message = Mock(spec=types.Message)
        message.text = "/start"
        message.chat = Mock()
        message.chat.id = 12345
        from_user = Mock()
        from_user.id = 67890
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user
        
        bot_service.bot.reply_to = Mock()

        # Act
        handler = None
        for registered_handler in bot_service.bot.message_handlers:
            if registered_handler['filters']['commands'] == ['start']:
                handler = registered_handler['function']
                break
        
        assert handler is not None
        # Should not raise exception
        handler(message)

        # Assert
        # Verify bot still replied (command should succeed even if user save fails)
        bot_service.bot.reply_to.assert_called_once()

    @patch('integrations.bale.bot_service.get_db_session')
    def test_start_command_handles_missing_from_user(self, mock_get_db_session, test_db):
        """Test /start command handles message without from_user gracefully."""
        # Arrange
        mock_get_db_session.return_value = test_db
        
        bot_service = BotService(token="123456:test_token", api_url="https://api.bale.ai")
        
        message = Mock(spec=types.Message)
        message.text = "/start"
        message.chat = Mock()
        message.chat.id = 12345
        message.from_user = None  # Missing from_user
        
        bot_service.bot.reply_to = Mock()

        # Act
        handler = None
        for registered_handler in bot_service.bot.message_handlers:
            if registered_handler['filters']['commands'] == ['start']:
                handler = registered_handler['function']
                break
        
        assert handler is not None
        # Should not raise exception
        handler(message)

        # Assert
        # Verify bot replied (should be called at least once with greeting)
        assert bot_service.bot.reply_to.called, "Bot should have replied"
        # Verify greeting was sent
        calls = bot_service.bot.reply_to.call_args_list
        greeting_sent = any("خوش آمدید" in str(call) for call in calls)
        assert greeting_sent, "Greeting message should have been sent"
        
        # Verify no user was saved (since from_user was None)
        repository = BotUserRepository(test_db)
        # Check that no users were created (or verify count is 0)
        user_count = test_db.query(BotUser).count()
        # This test assumes database starts empty, adjust if needed
        assert user_count == 0
