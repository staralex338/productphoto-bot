"""
ProductPhoto AI — Telegram Bot for AI Product Photography

This is the main application entry point.
It sets up FastAPI, aiogram bot, database connection, and webhook handlers.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import get_settings

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Global bot and dispatcher instances (initialized in lifespan)
bot: Bot | None = None
dp: Dispatcher | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Steps on startup:
      1. Initialize aiogram Bot and Dispatcher.
      2. Set up Telegram webhook (if in production).
      3. Connect to database.

    Steps on shutdown:
      1. Delete Telegram webhook (optional).
      2. Close database connections.
    """
    global bot, dp

    logger.info("🚀 Starting up %s...", settings.app_name)

    # 1. Create bot instance with FSM storage
    storage = MemoryStorage()
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Register aiogram handlers
    from app.bot.handlers import register_handlers
    register_handlers(dp)
    logger.info("Bot handlers registered.")

    # 2. Set Telegram webhook in production
    if settings.is_production:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != settings.telegram_webhook_url:
            await bot.set_webhook(
                url=settings.telegram_webhook_url,
                secret_token=settings.telegram_webhook_secret or None,
            )
            logger.info("Webhook set to %s", settings.telegram_webhook_url)
    else:
        logger.info("Development mode: webhook not set. Use polling or ngrok.")

    # 3. Initialize database connection
    from app.database.engine import init_db
    await init_db()
    logger.info("Database connected.")

    # 4. Start background cleanup task for task queue
    from app.bot.services.task_queue import get_task_queue

    async def cleanup_loop():
        """Periodically clean completed tasks from queue to prevent memory leaks."""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            queue = get_task_queue()
            removed = queue.cleanup_old_tasks(max_age_seconds=1800)  # Remove tasks older than 30 min
            if removed:
                logger.info("Cleaned up %d old tasks from queue", removed)

    cleanup_task = asyncio.create_task(cleanup_loop())

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("🛑 Shutting down %s...", settings.app_name)

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    if bot:
        await bot.session.close()
        logger.info("Bot session closed.")

    # Close database connection
    from app.database.engine import close_db
    await close_db()
    logger.info("Database connection closed.")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered product photography Telegram bot",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for monitoring and Docker healthcheck."""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Receive updates from Telegram via webhook.

    In production, Telegram sends updates to this endpoint.
    We validate the secret token (if configured) and pass the update to aiogram.
    """
    # Validate secret token
    if settings.telegram_webhook_secret:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != settings.telegram_webhook_secret:
            logger.warning("Invalid webhook secret token received")
            return Response(status_code=status.HTTP_403_FORBIDDEN)

    if not bot or not dp:
        logger.error("Bot or Dispatcher not initialized")
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Parse update and feed to aiogram
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Error processing Telegram update: %s", e)
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/")
async def root():
    """Root endpoint with basic app info."""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/webhook/fal")
async def fal_webhook(request: Request):
    """
    Receive Fal.ai async generation results via webhook.

    Fal.ai can send results here when using async queue mode.
    In our current implementation, we use synchronous API calls
    via fal_client.submit_async, so this is reserved for future use
    or for handling Fal.ai queue callbacks.
    """
    try:
        data = await request.json()
        logger.info("Received Fal.ai webhook: %s", data)
        # TODO: Handle async Fal.ai callbacks if switching to queue mode
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Error processing Fal.ai webhook: %s", e)
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/admin/queue")
async def queue_status():
    """Admin endpoint to check task queue status."""
    from app.bot.services.task_queue import get_task_queue

    queue = get_task_queue()
    return {
        "max_concurrent": queue.max_concurrent,
        "active_tasks": queue.get_active_count(),
        "pending_tasks": queue.get_pending_count(),
        "total_tracked": len(queue._tasks),
    }


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Receive Stripe payment events via webhook.

    Handles checkout.session.completed events to credit user accounts.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        logger.warning("Stripe webhook missing signature")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        from app.payments.stripe_client import handle_stripe_webhook
        result = await handle_stripe_webhook(payload, signature)
        return result
    except ValueError as e:
        logger.warning("Stripe webhook validation error: %s", e)
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Stripe webhook processing error: %s", e)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
