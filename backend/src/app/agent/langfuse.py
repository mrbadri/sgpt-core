import logging
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from app.config.langfuse_settings import get_langfuse_settings

logger = logging.getLogger(__name__)

_settings = get_langfuse_settings()

# Apply settings to env only if not already set (env vars take precedence)
import os
if _settings.langfuse_public_key:
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", _settings.langfuse_public_key)
if _settings.langfuse_secret_key:
    os.environ.setdefault("LANGFUSE_SECRET_KEY", _settings.langfuse_secret_key)
if _settings.langfuse_base_url:
    os.environ.setdefault("LANGFUSE_BASE_URL", _settings.langfuse_base_url)
elif _settings.langfuse_host:
    os.environ.setdefault("LANGFUSE_HOST", _settings.langfuse_host)

langfuse = get_client()

try:
    if langfuse.auth_check():
        logger.info("Langfuse client is authenticated and ready!")
    else:
        logger.warning("Langfuse authentication failed. Tracing will be disabled.")
except Exception as exc:
    logger.warning("Langfuse unreachable (%s). Tracing will be disabled.", exc)

langfuse_handler = CallbackHandler()
