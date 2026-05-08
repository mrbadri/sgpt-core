"""Register all Bale bot message handlers."""

from __future__ import annotations

from integrations.bale.handlers.contact import register_contact_handler
from integrations.bale.handlers.deep_chat import register_deep_chat_handler
from integrations.bale.handlers.deps import BaleHandlerDeps
from integrations.bale.handlers.fallback import register_fallback_handler
from integrations.bale.handlers.start import register_start_handler

__all__ = ["BaleHandlerDeps", "register_handlers"]


def register_handlers(deps: BaleHandlerDeps) -> None:
    register_start_handler(deps)
    register_contact_handler(deps)
    register_deep_chat_handler(deps)
    register_fallback_handler(deps)
