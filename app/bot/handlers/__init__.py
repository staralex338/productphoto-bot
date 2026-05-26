"""
Register all aiogram routers.

Import and include routers for commands, photos, callbacks, and payments.
"""

from aiogram import Dispatcher

from app.bot.handlers.commands import router as commands_router
from app.bot.handlers.photos import router as photos_router
from app.bot.handlers.callbacks import router as callbacks_router
from app.bot.handlers.payments import router as payments_router


def register_handlers(dp: Dispatcher) -> None:
    """
    Register all bot handlers with the dispatcher.

    Order matters: more specific filters should come first.
    """
    dp.include_router(commands_router)
    dp.include_router(photos_router)
    dp.include_router(callbacks_router)
    dp.include_router(payments_router)
