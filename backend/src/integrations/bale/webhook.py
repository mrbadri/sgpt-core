"""Bale webhook handler."""

from typing import Dict, Any
from fastapi import Request


async def handle_webhook(request: Request) -> Dict[str, Any]:
    """Handle incoming webhook from Bale."""
    # TODO: Implement webhook handling logic
    data = await request.json()
    return {"status": "received"}


def verify_webhook_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    """Verify webhook signature."""
    # TODO: Implement signature verification
    return True
