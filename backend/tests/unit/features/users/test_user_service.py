"""Tests for bot user service."""

from unittest.mock import Mock, MagicMock, patch
import pytest
from telebot import types

from features.users.models import BotUser
from features.users.service import BotUserService
from features.users.schemas import BotUserCreate


class TestBotUserService:
    """Test suite for BotUserService."""

    def test_save_user_from_message_success_new_user(self, test_db):
        """Test saving user from message creates new user."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        from_user = Mock()
        from_user.id = 12345
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user

        # Act
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert created is True
        assert db_user is not None
        assert db_user.bale_user_id == 12345
        assert db_user.username == "testuser"
        assert db_user.first_name == "Test"
        assert db_user.last_name == "User"
        assert db_user.is_bot is False
        assert db_user.language_code == "en"

    def test_save_user_from_message_existing_user(self, test_db):
        """Test saving user from message returns existing user."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        from_user = Mock()
        from_user.id = 12345
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user

        # Create user first
        service.save_user_from_message(message)

        # Act - try to save again
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert created is False
        assert db_user is not None
        assert db_user.bale_user_id == 12345

    def test_save_user_from_message_no_from_user(self, test_db):
        """Test saving user from message with no from_user returns None."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        message.from_user = None

        # Act
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert db_user is None
        assert created is False

    def test_save_user_from_message_minimal_data(self, test_db):
        """Test saving user with minimal data (no optional fields)."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        
        # Create a simple class to simulate user without language_code attribute
        class MinimalUser:
            def __init__(self):
                self.id = 12345
                self.username = None
                self.first_name = None
                self.last_name = None
                self.is_bot = False
        
        from_user = MinimalUser()
        message.from_user = from_user

        # Act
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert created is True
        assert db_user is not None
        assert db_user.bale_user_id == 12345
        assert db_user.username is None
        assert db_user.first_name is None
        assert db_user.last_name is None
        assert db_user.is_bot is False
        assert db_user.language_code is None

    def test_save_user_from_message_without_is_bot_attribute(self, test_db):
        """Test saving user when is_bot attribute is missing."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        
        # Create a simple class to simulate user without is_bot attribute
        class UserWithoutIsBot:
            def __init__(self):
                self.id = 12345
                self.username = "testuser"
                self.first_name = "Test"
                self.last_name = "User"
                self.language_code = "en"
        
        from_user = UserWithoutIsBot()
        message.from_user = from_user

        # Act
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert created is True
        assert db_user is not None
        assert db_user.bale_user_id == 12345
        assert db_user.is_bot is False  # Should default to False

    def test_save_user_from_message_without_language_code_attribute(self, test_db):
        """Test saving user when language_code attribute is missing."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        
        # Create a simple class to simulate user without language_code attribute
        class UserWithoutLanguageCode:
            def __init__(self):
                self.id = 12345
                self.username = "testuser"
                self.first_name = "Test"
                self.last_name = "User"
                self.is_bot = False
        
        from_user = UserWithoutLanguageCode()
        message.from_user = from_user

        # Act
        db_user, created = service.save_user_from_message(message)

        # Assert
        assert created is True
        assert db_user is not None
        assert db_user.bale_user_id == 12345
        assert db_user.language_code is None

    def test_save_user_from_message_idempotent(self, test_db):
        """Test save_user_from_message is idempotent."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        from_user = Mock()
        from_user.id = 12345
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user

        # Act - save multiple times
        user1, created1 = service.save_user_from_message(message)
        user2, created2 = service.save_user_from_message(message)
        user3, created3 = service.save_user_from_message(message)

        # Assert
        assert user1.id == user2.id == user3.id
        assert created1 is True
        assert created2 is False
        assert created3 is False

    def test_save_user_from_message_database_error(self, test_db):
        """Test save_user_from_message raises exception on database error."""
        # Arrange
        service = BotUserService(test_db)
        message = Mock(spec=types.Message)
        from_user = Mock()
        from_user.id = 12345
        from_user.username = "testuser"
        from_user.first_name = "Test"
        from_user.last_name = "User"
        from_user.is_bot = False
        from_user.language_code = "en"
        message.from_user = from_user

        # Mock repository.get_or_create to raise an exception
        with patch.object(service.repository, 'get_or_create', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception, match="Database error"):
                service.save_user_from_message(message)
