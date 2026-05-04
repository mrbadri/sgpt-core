"""Cryptographic utilities."""

import hashlib
import secrets
from typing import Optional


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_string(value: str) -> str:
    """Hash a string using SHA-256."""
    return hashlib.sha256(value.encode()).hexdigest()


def verify_hash(value: str, hash_value: str) -> bool:
    """Verify a string against a hash."""
    return hash_string(value) == hash_value


def generate_secret_key() -> str:
    """Generate a secret key for signing."""
    return secrets.token_urlsafe(32)
