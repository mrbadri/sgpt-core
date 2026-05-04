"""Bale signature verification utilities."""

import hmac
import hashlib
from typing import Optional


def verify_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    """Verify Bale webhook signature."""
    # TODO: Implement proper signature verification
    # This should match Bale's signature algorithm
    expected_signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate signature for payload."""
    return hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
