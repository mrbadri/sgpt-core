"""Models package."""

from app.models.base import (
    BaseDBModel,
    BaseDBModelUUID,
    BaseDBModelWithSoftDelete,
)
from app.models.identity import UserIdentity
from app.models.message import BaleMessage, Message
from app.models.payment import BalePayment, Payment
from app.models.subscription import UserSubscription
from app.models.user import User

# Export all models for Alembic
__all__ = [
    "BaseDBModel",
    "BaseDBModelUUID",
    "BaseDBModelWithSoftDelete",
    "UserIdentity",
    "Message",
    "BaleMessage",
    "Payment",
    "BalePayment",
    "UserSubscription",
    "User",
]
