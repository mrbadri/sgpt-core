"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import logging as app_logging
from app.errors.handlers import (
    application_error_handler,
    general_exception_handler,
)
from app.errors.base import ApplicationError
from app.settings import settings

# Import routers conditionally to avoid errors if routes don't exist yet
try:
    from app.api.bot.router import router as bot_router
except ImportError:
    from fastapi import APIRouter
    bot_router = APIRouter()




# Initialize logging
app_logging.setup_logging()
logger = app_logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize services
    if settings.bale_bot_token:
        try:
            from integrations.bale.bot_service import initialize_bot_service

            print("\n" + "="*60)
            print("🚀 INITIALIZING BOT SERVICE...")
            print("="*60 + "\n")
            
            bot_service = initialize_bot_service()
            await bot_service.start_polling()
            logger.info("Bot service started successfully")
        except Exception as e:
            print("\n" + "="*60)
            print("❌ BOT SERVICE INITIALIZATION FAILED")
            print("="*60)
            print(f"Error: {e}")
            print("="*60 + "\n")
            
            logger.error(f"Failed to start bot service: {e}", exc_info=True)
            # Don't fail application startup if bot fails
    else:
        print("\n" + "="*60)
        print("⚠️  BOT STATUS: NOT CONFIGURED")
        print("="*60)
        print("BALE_BOT_TOKEN not set in environment variables")
        print("Bot service will not start")
        print("="*60 + "\n")
        
        logger.warning("BALE_BOT_TOKEN not configured, bot service will not start")

    yield

    # Shutdown: Cleanup services
    from integrations.bale.bot_service import get_bot_service

    bot_service = get_bot_service()
    if bot_service:
        try:
            await bot_service.stop_polling()
            logger.info("Bot service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot service: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register routers
app.include_router(bot_router, prefix="/api/bot", tags=["bot"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}





if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
