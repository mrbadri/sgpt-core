"""Bale bot service for handling commands and messages."""

import asyncio
import logging
import threading
from typing import Optional, Callable, Any
import telebot
from telebot import apihelper
from telebot import types

from app.settings import settings
from app import logging as app_logging
from app.db.session import get_db_session
from features.users.service import BotUserService

logger = app_logging.get_logger(__name__)


class BotService:
    """Service for managing Bale bot operations."""

    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize bot service with token and API URL from settings."""
        self.token = token or settings.bale_bot_token
        self.api_url = api_url or settings.bale_api_url

        if not self.token:
            raise ValueError("BALE_BOT_TOKEN must be set in environment variables")

        # Configure Bale API URL (Telegram-compatible format)
        apihelper.API_URL = self.api_url

        # Initialize bot instance
        self.bot = telebot.TeleBot(self.token)
        self._polling_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._stop_event = threading.Event()

        # Register command handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register command handlers for the bot."""
        # Start command handler
        @self.bot.message_handler(commands=["start"])
        def handle_start(message: types.Message) -> None:
            """Handle /start command."""
            try:
                payload = None

                # Parse deep-link payload: /start <payload>
                if message.text:
                    parts = message.text.split(maxsplit=1)
                    if len(parts) == 2:
                        payload = parts[1]

                # Save user to database (idempotent - won't create duplicate)
                try:
                    db = get_db_session()
                    try:
                        user_service = BotUserService(db)
                        db_user, created = user_service.save_user_from_message(message)
                        if db_user:
                            logger.debug(
                                f"User saved | bale_user_id={db_user.bale_user_id} "
                                f"created={created}"
                            )
                    except Exception as user_error:
                        # Log error but don't fail the /start command
                        logger.error(
                            f"Error saving user to database: {user_error}",
                            exc_info=True
                        )
                    finally:
                        db.close()
                except Exception as db_error:
                    # Log database session error but don't fail the /start command
                    logger.error(
                        f"Error creating database session: {db_error}",
                        exc_info=True
                    )

                greeting = "سلام! 👋\n\nخوش آمدید به ربات بله!"
                if payload:
                    greeting += f"\n\npayload: {payload}"

                self.bot.reply_to(message, greeting)

                user_id = message.from_user.id if message.from_user else None
                logger.info(
                    f"/start received | user_id={user_id} "
                    f"chat_id={message.chat.id} payload={payload}"
                )

            except Exception as e:
                logger.error(f"Error handling start command: {e}", exc_info=True)
                try:
                    self.bot.reply_to(
                        message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
                    )
                except Exception:
                    pass


        # Echo command handler
        @self.bot.message_handler(commands=["echo"])
        def handle_echo(message: types.Message) -> None:
            """Handle /echo command."""
            try:
                text = message.text.replace("/echo", "").strip()
                if text:
                    self.bot.reply_to(message, text)
                    logger.info(
                        f"Echo command received from user {message.from_user.id}: {text}"
                    )
                else:
                    usage_message = "یه متن بده: /echo سلام"
                    self.bot.reply_to(message, usage_message)
            except Exception as e:
                logger.error(f"Error handling echo command: {e}", exc_info=True)
                try:
                    self.bot.reply_to(
                        message, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
                    )
                except Exception:
                    pass

        # Unknown command handler
        @self.bot.message_handler(func=lambda m: True)
        def handle_unknown(message: types.Message) -> None:
            """Handle unknown commands and messages."""
            try:
                # Only respond to commands (messages starting with /)
                if message.text and message.text.startswith("/"):
                    logger.warning(
                        f"Unknown command received from user {message.from_user.id}: {message.text}"
                    )
                    # Don't reply to unknown commands to avoid spam
                    # The bot will silently ignore them
            except Exception as e:
                logger.error(f"Error handling unknown command: {e}", exc_info=True)

    async def start_polling(self) -> None:
        """Start bot polling in background."""
        if self._is_running:
            logger.warning("Bot polling is already running")
            return

        self._is_running = True
        self._stop_event.clear()
        logger.info("Starting bot polling...")

        def run_polling() -> None:
            """Run bot polling in blocking mode."""
            try:
                logger.info("Bot polling thread started")
                # Test bot connection first
                try:
                    bot_info = self.bot.get_me()
                    bot_username = bot_info.username if hasattr(bot_info, 'username') else 'Unknown'
                    bot_id = bot_info.id if hasattr(bot_info, 'id') else 'Unknown'
                    
                    # Big status print
                    print("\n" + "="*60)
                    print("🤖 BOT STATUS: RUNNING ✅")
                    print("="*60)
                    print(f"Bot Username: @{bot_username}")
                    print(f"Bot ID: {bot_id}")
                    print(f"API URL: {self.api_url}")
                    print("="*60 + "\n")
                    
                    logger.info(f"Bot connected successfully: @{bot_username} (ID: {bot_id})")
                except Exception as e:
                    # Big error print
                    print("\n" + "="*60)
                    print("❌ BOT STATUS: FAILED TO START")
                    print("="*60)
                    print(f"Error: {e}")
                    print("="*60 + "\n")
                    
                    logger.error(f"Failed to connect to bot API: {e}", exc_info=True)
                    self._is_running = False
                    return
                
                self.bot.infinity_polling(none_stop=True, timeout=20, long_polling_timeout=20)
                logger.info("Bot polling thread ended")
            except Exception as e:
                # Big error print
                print("\n" + "="*60)
                print("❌ BOT STATUS: ERROR IN POLLING")
                print("="*60)
                print(f"Error: {e}")
                print("="*60 + "\n")
                
                logger.error(f"Error in bot polling: {e}", exc_info=True)
                self._is_running = False
            finally:
                self._is_running = False

        # Run polling in a separate thread to avoid blocking FastAPI
        self._polling_thread = threading.Thread(
            target=run_polling,
            name="BotPollingThread",
            daemon=True
        )
        self._polling_thread.start()
        
        # Give the thread a moment to start
        await asyncio.sleep(0.5)
        
        if self._polling_thread.is_alive():
            logger.info("Bot polling started successfully")
        else:
            # Big error print
            print("\n" + "="*60)
            print("❌ BOT STATUS: THREAD FAILED TO START")
            print("="*60)
            print("The bot polling thread did not start properly.")
            print("Check logs for more details.")
            print("="*60 + "\n")
            
            logger.error("Bot polling thread failed to start")
            self._is_running = False

    async def stop_polling(self) -> None:
        """Stop bot polling gracefully."""
        if not self._is_running:
            logger.info("Bot polling is not running")
            return

        print("\n" + "="*60)
        print("🛑 BOT STATUS: STOPPING...")
        print("="*60 + "\n")
        
        logger.info("Stopping bot polling...")
        self._is_running = False
        self._stop_event.set()

        try:
            # Stop the bot polling
            self.bot.stop_polling()

            # Wait for polling thread to complete
            if self._polling_thread and self._polling_thread.is_alive():
                # Wait up to 5 seconds for thread to finish
                self._polling_thread.join(timeout=5.0)
                if self._polling_thread.is_alive():
                    logger.warning("Timeout waiting for bot polling thread to stop")
                else:
                    logger.info("Bot polling thread stopped")
        except Exception as e:
            logger.error(f"Error stopping bot polling: {e}", exc_info=True)

        print("\n" + "="*60)
        print("🛑 BOT STATUS: STOPPED")
        print("="*60 + "\n")
        
        logger.info("Bot polling stopped successfully")

    def is_running(self) -> bool:
        """Check if bot polling is running."""
        return self._is_running


# Global bot service instance
_bot_service: Optional[BotService] = None


def get_bot_service() -> Optional[BotService]:
    """Get the global bot service instance."""
    return _bot_service


def initialize_bot_service() -> BotService:
    """Initialize the global bot service instance."""
    global _bot_service
    if _bot_service is None:
        _bot_service = BotService()
    return _bot_service
