"""Bot API router."""

from fastapi import APIRouter

from app.api.bot.routes import (
    health,
)

router = APIRouter()

# Register route modules
router.include_router(health.router)
