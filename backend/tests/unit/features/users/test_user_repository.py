"""Tests for bot user repository."""

import pytest
from sqlalchemy.exc import IntegrityError

from features.users.models import BotUser
from features.users.repository import BotUserRepository
from features.users.schemas import BotUserCreate


class TestBotUserRepository:
    """Test suite for BotUserRepository."""

    def test_get_by_bale_user_id_exists(self, test_db):
        """Test getting user by Bale user ID when user exists."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )
        created_user = repository.create(user_data)

        # Act
        found_user = repository.get_by_bale_user_id(12345)

        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.bale_user_id == 12345
        assert found_user.username == "testuser"
        assert found_user.first_name == "Test"
        assert found_user.last_name == "User"
        assert found_user.is_bot is False
        assert found_user.language_code == "en"

    def test_get_by_bale_user_id_not_exists(self, test_db):
        """Test getting user by Bale user ID when user doesn't exist."""
        # Arrange
        repository = BotUserRepository(test_db)

        # Act
        found_user = repository.get_by_bale_user_id(99999)

        # Assert
        assert found_user is None

    def test_create_user_success(self, test_db):
        """Test creating a new user successfully."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )

        # Act
        created_user = repository.create(user_data)

        # Assert
        assert created_user.id is not None
        assert created_user.bale_user_id == 12345
        assert created_user.username == "testuser"
        assert created_user.first_name == "Test"
        assert created_user.last_name == "User"
        assert created_user.is_bot is False
        assert created_user.language_code == "en"
        assert created_user.created_at is not None
        assert created_user.updated_at is not None

    def test_create_user_with_minimal_data(self, test_db):
        """Test creating user with only required fields."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username=None,
            first_name=None,
            last_name=None,
            is_bot=False,
            language_code=None,
        )

        # Act
        created_user = repository.create(user_data)

        # Assert
        assert created_user.id is not None
        assert created_user.bale_user_id == 12345
        assert created_user.username is None
        assert created_user.first_name is None
        assert created_user.last_name is None
        assert created_user.is_bot is False
        assert created_user.language_code is None

    def test_create_user_duplicate_bale_user_id(self, test_db):
        """Test creating user with duplicate Bale user ID raises error."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )
        repository.create(user_data)

        # Act & Assert
        with pytest.raises(IntegrityError):
            repository.create(user_data)

    def test_get_or_create_existing_user(self, test_db):
        """Test get_or_create returns existing user when user exists."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )
        original_user = repository.create(user_data)

        # Act
        user, created = repository.get_or_create(user_data)

        # Assert
        assert created is False
        assert user.id == original_user.id
        assert user.bale_user_id == 12345

    def test_get_or_create_new_user(self, test_db):
        """Test get_or_create creates new user when user doesn't exist."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )

        # Act
        user, created = repository.get_or_create(user_data)

        # Assert
        assert created is True
        assert user.id is not None
        assert user.bale_user_id == 12345
        assert user.username == "testuser"

    def test_get_or_create_idempotent(self, test_db):
        """Test get_or_create is idempotent - multiple calls return same user."""
        # Arrange
        repository = BotUserRepository(test_db)
        user_data = BotUserCreate(
            bale_user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
            language_code="en",
        )

        # Act
        user1, created1 = repository.get_or_create(user_data)
        user2, created2 = repository.get_or_create(user_data)
        user3, created3 = repository.get_or_create(user_data)

        # Assert
        assert user1.id == user2.id == user3.id
        assert created1 is True
        assert created2 is False
        assert created3 is False
