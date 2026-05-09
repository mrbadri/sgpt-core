"""Versioned REST endpoints for health and bot runtime status (web/mobile clients)."""

from fastapi import APIRouter

from app.settings import settings

router = APIRouter()


@router.get("/health-check")
async def health_check():
    """API v1 health check."""
    return {"status": "healthy", "api": "v1"}


@router.get("/bot/status")
async def bot_status():
    """Bale bot service status."""
    from integrations.bale.bot_service import get_bot_service

    bot_service = get_bot_service()
    if bot_service:
        is_running = bot_service.is_running()
        return {
            "bot_configured": True,
            "bot_running": is_running,
            "status": "RUNNING ✅" if is_running else "STOPPED ❌",
        }
    return {
        "bot_configured": bool(settings.bale_bot_token),
        "bot_running": False,
        "status": "NOT CONFIGURED ⚠️"
        if not settings.bale_bot_token
        else "NOT INITIALIZED ❌",
    }
