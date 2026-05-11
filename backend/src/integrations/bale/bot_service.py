"""Bale bot service for handling commands and messages."""

import asyncio
import threading
from typing import Optional

import requests as _requests
import telebot
from telebot import apihelper

from app import logging as app_logging
from app.services.agent_bridge import BaleAgentBridge
from app.settings import settings
from integrations.bale.handlers import register_handlers
from integrations.bale.handlers.deps import BaleHandlerDeps
from integrations.bale.messaging import reply_long_text

logger = app_logging.get_logger(__name__)


def _bale_request_sender(method, url, params=None, files=None, timeout=None, proxies=None):
    """Send POST payloads in the request body to avoid URI-Too-Large errors.

    pyTelegramBotAPI passes params= to requests.request(), which always encodes
    them into the URL query string.  For long Persian text that URL-encodes to
    ~6 bytes per character this exceeds nginx's default URI limit (8 KB) on
    tapi.bale.ai and causes 414 responses.  Moving the payload to the POST body
    fixes the issue without changing chunk sizes.
    """
    if method.lower() == "post":
        if files:
            return _requests.request(
                method, url, data=params, files=files, timeout=timeout, proxies=proxies
            )
        if params:
            return _requests.request(
                method, url, data=params, timeout=timeout, proxies=proxies
            )
    return _requests.request(
        method, url, params=params, files=files, timeout=timeout, proxies=proxies
    )


class BotService:
    """Service for managing Bale bot operations."""

    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize bot service with token and API URL from settings."""
        self.token = token or settings.bale_bot_token
        self.api_url = api_url or settings.bale_api_url

        if not self.token:
            raise ValueError("BALE_BOT_TOKEN must be set in environment variables")

        apihelper.API_URL = self.api_url
        apihelper.CUSTOM_REQUEST_SENDER = _bale_request_sender

        self.bot = telebot.TeleBot(self.token)
        self._polling_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._stop_event = threading.Event()

        self._agent_bridge = BaleAgentBridge()

        deps = BaleHandlerDeps(
            bot=self.bot,
            logger=logger,
            agent_bridge=self._agent_bridge,
            reply_long_text=lambda m, t: reply_long_text(self.bot, m, t),
            payment_provider_token=settings.bale_payment_provider_token,
            api_url=self.api_url,
        )
        register_handlers(deps)

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
                try:
                    bot_info = self.bot.get_me()
                    bot_username = bot_info.username if hasattr(bot_info, "username") else "Unknown"
                    bot_id = bot_info.id if hasattr(bot_info, "id") else "Unknown"

                    print("\n" + "=" * 60)
                    print("🤖 BOT STATUS: RUNNING ✅")
                    print("=" * 60)
                    print(f"Bot Username: @{bot_username}")
                    print(f"Bot ID: {bot_id}")
                    print(f"API URL: {self.api_url}")
                    print("=" * 60 + "\n")

                    logger.info(f"Bot connected successfully: @{bot_username} (ID: {bot_id})")
                except Exception as e:
                    print("\n" + "=" * 60)
                    print("❌ BOT STATUS: FAILED TO START")
                    print("=" * 60)
                    print(f"Error: {e}")
                    print("=" * 60 + "\n")

                    logger.error(f"Failed to connect to bot API: {e}", exc_info=True)
                    self._is_running = False
                    return

                self.bot.infinity_polling(none_stop=True, timeout=20, long_polling_timeout=20)
                logger.info("Bot polling thread ended")
            except Exception as e:
                print("\n" + "=" * 60)
                print("❌ BOT STATUS: ERROR IN POLLING")
                print("=" * 60)
                print(f"Error: {e}")
                print("=" * 60 + "\n")

                logger.error(f"Error in bot polling: {e}", exc_info=True)
                self._is_running = False
            finally:
                self._is_running = False

        self._polling_thread = threading.Thread(
            target=run_polling,
            name="BotPollingThread",
            daemon=True,
        )
        self._polling_thread.start()

        await asyncio.sleep(0.5)

        if self._polling_thread.is_alive():
            logger.info("Bot polling started successfully")
        else:
            print("\n" + "=" * 60)
            print("❌ BOT STATUS: THREAD FAILED TO START")
            print("=" * 60)
            print("The bot polling thread did not start properly.")
            print("Check logs for more details.")
            print("=" * 60 + "\n")

            logger.error("Bot polling thread failed to start")
            self._is_running = False

    async def stop_polling(self) -> None:
        """Stop bot polling gracefully."""
        if not self._is_running:
            logger.info("Bot polling is not running")
            return

        print("\n" + "=" * 60)
        print("🛑 BOT STATUS: STOPPING...")
        print("=" * 60 + "\n")

        logger.info("Stopping bot polling...")
        self._is_running = False
        self._stop_event.set()

        try:
            self.bot.stop_polling()

            if self._polling_thread and self._polling_thread.is_alive():
                self._polling_thread.join(timeout=5.0)
                if self._polling_thread.is_alive():
                    logger.warning("Timeout waiting for bot polling thread to stop")
                else:
                    logger.info("Bot polling thread stopped")
        except Exception as e:
            logger.error(f"Error stopping bot polling: {e}", exc_info=True)

        print("\n" + "=" * 60)
        print("🛑 BOT STATUS: STOPPED")
        print("=" * 60 + "\n")

        logger.info("Bot polling stopped successfully")

    def is_running(self) -> bool:
        """Check if bot polling is running."""
        return self._is_running


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
