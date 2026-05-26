"""
Admin handlers for bot owner.

Telegram ID: 1003330009
Provides dashboard, user management, broadcast, etc.
"""

import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func

from app.bot.i18n import Translator
from app.bot.keyboards import admin_dashboard_keyboard, admin_main_menu_keyboard
from app.database import AsyncSessionLocal
from app.database.repositories import (
    GenerationRepository,
    PaymentRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)
router = Router()

# Admin Telegram ID
ADMIN_TELEGRAM_ID = 1003330009


def is_admin(telegram_id: int) -> bool:
    """Check if user is bot owner."""
    return telegram_id == ADMIN_TELEGRAM_ID


# =============================================================================
# /admin command
# =============================================================================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Show admin dashboard."""
    if not is_admin(message.from_user.id):
        return  # Silently ignore for non-admins

    await show_dashboard(message)


# =============================================================================
# Dashboard
# =============================================================================

async def show_dashboard(message_or_callback):
    """Build and send admin dashboard."""
    t = Translator("ru")  # Admin always sees Russian

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        gen_repo = GenerationRepository(session)
        payment_repo = PaymentRepository(session)

        # Users
        total_users = await user_repo.get_total_users()
        new_today = await user_repo.get_new_users_count(today_start)
        new_week = await user_repo.get_new_users_count(week_start)
        new_month = await user_repo.get_new_users_count(month_start)

        # Generations
        total_generations = await gen_repo.get_total_generations()
        gen_today = await gen_repo.get_generations_count(today_start)

        # Revenue (only completed payments)
        total_revenue = await payment_repo.get_total_revenue()
        revenue_today = await payment_repo.get_revenue(today_start)

    # Build text
    text = t.t(
        "admin_dashboard",
        total_users=total_users,
        new_today=new_today,
        new_week=new_week,
        new_month=new_month,
        total_generations=total_generations,
        gen_today=gen_today,
        total_revenue=f"{total_revenue:.2f}",
        revenue_today=f"{revenue_today:.2f}",
    )

    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.edit_text(
            text,
            reply_markup=admin_dashboard_keyboard(),
        )
    else:
        await message_or_callback.answer(
            text,
            reply_markup=admin_dashboard_keyboard(),
        )


# =============================================================================
# Admin Callbacks
# =============================================================================

@router.callback_query(F.data == "admin:dashboard")
async def on_admin_dashboard(callback: CallbackQuery):
    """Refresh dashboard."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    await show_dashboard(callback.message)
    await callback.answer("🔄 Обновлено")


@router.callback_query(F.data == "admin:users")
async def on_admin_users(callback: CallbackQuery):
    """Show users management (placeholder for next phase)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    t = Translator("ru")
    await callback.message.edit_text(
        t.t("admin_users_title"),
        reply_markup=admin_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:generations")
async def on_admin_generations(callback: CallbackQuery):
    """Show generations management (placeholder for next phase)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    t = Translator("ru")
    await callback.message.edit_text(
        t.t("admin_generations_title"),
        reply_markup=admin_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def on_admin_broadcast(callback: CallbackQuery):
    """Show broadcast menu (placeholder for next phase)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    t = Translator("ru")
    await callback.message.edit_text(
        t.t("admin_broadcast_title"),
        reply_markup=admin_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:back")
async def on_admin_back(callback: CallbackQuery):
    """Return to admin dashboard."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    await show_dashboard(callback.message)
    await callback.answer()
