import logging
import os
from contextlib import contextmanager
from typing import Generator

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from app.config.langfuse_settings import get_langfuse_settings

logger = logging.getLogger(__name__)

_settings = get_langfuse_settings()

# Apply settings to env only if not already set (env vars take precedence)
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


def create_langfuse_handler() -> CallbackHandler:
    return CallbackHandler()


@contextmanager
def langfuse_trace_context(
    user_id: str | None = None,
    channel: str | None = None,
    provider: str | None = None,
    provider_user_id: str | None = None,
    extra_metadata: dict | None = None,
) -> Generator[None, None, None]:
    """Context manager that propagates per-request trace attributes (langfuse v4+)."""
    metadata: dict = {}
    if channel:
        metadata["channel"] = channel
    if provider:
        metadata["provider"] = provider
    if provider_user_id:
        metadata["provider_user_id"] = provider_user_id
    if extra_metadata:
        metadata.update(extra_metadata)

    session_id = (
        f"{provider}-{provider_user_id}"
        if provider and provider_user_id
        else f"user-{user_id}" if user_id else None
    )

    with propagate_attributes(
        trace_name="deep-agent",
        user_id=str(user_id) if user_id else None,
        session_id=session_id,
        metadata=metadata or None,
        tags=[_settings.environment],
    ):
        yield
