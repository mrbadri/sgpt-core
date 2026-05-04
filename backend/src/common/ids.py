"""ID generation utilities."""

import uuid
from typing import Optional


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """Generate a short ID."""
    return uuid.uuid4().hex[:12]


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False
