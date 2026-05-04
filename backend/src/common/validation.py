"""Validation utilities."""

import re
from typing import Optional


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    # Basic phone validation - adjust regex as needed
    pattern = r"^\+?[1-9]\d{1,14}$"
    return bool(re.match(pattern, phone))


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input."""
    sanitized = value.strip()
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
