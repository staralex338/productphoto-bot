"""
Admin handlers for bot owner.

Telegram ID: 1003330009
Provides dashboard, user management, broadcast, etc.
"""

import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func

from app.bot.i18n import Translator
from app.bot.keyboards import (
    admin_dashboard_keyboard,
    admin_main_menu_keyboard,
    admin_user_detail_keyboard,
    admin_user_history_keyboard,
    admin_users_list_keyboard,
)
from app.bot.states import AdminSearch
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
USERS_PER_PAGE = 10


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


@router.callback_query(F.data == "admin:dashboard")
async def on_admin_dashboard(callback: CallbackQuery):
    """Refresh dashboard."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    await show_dashboard(callback.message)
    await callback.answer("🔄 Обновлено")


# =============================================================================
# Users List
# =============================================================================

@router.callback_query(F.data == "admin:users")
async def on_admin_users(callback: CallbackQuery):
    """Show users list page 0."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    await show_users_page(callback.message, page=0)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:users:(\d+)$"))
async def on_admin_users_page(callback: CallbackQuery):
    """Show specific users page."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    page = int(callback.data.split(":")[2])
    await show_users_page(callback.message, page=page)
    await callback.answer()


async def show_users_page(message_or_callback, page: int = 0):
    """Show paginated list of users."""
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)

        # Get total count for pagination
        total_users = await user_repo.get_total_users()
        total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

        # Get users for current page
        users = await user_repo.get_users_paginated(
            offset=page * USERS_PER_PAGE,
            limit=USERS_PER_PAGE,
        )

    if not users:
        text = t.t("admin_users_list", page=1, total=1) + "\n\n<i>Пользователей пока нет</i>"
    else:
        text = t.t("admin_users_list", page=page + 1, total=total_pages)

    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.edit_text(
            text,
            reply_markup=admin_users_list_keyboard(users, page, total_pages),
        )
    else:
        await message_or_callback.answer(
            text,
            reply_markup=admin_users_list_keyboard(users, page, total_pages),
        )


# =============================================================================
# User Search
# =============================================================================

@router.callback_query(F.data == "admin:users:search")
async def on_admin_users_search(callback: CallbackQuery, state: FSMContext):
    """Start user search flow."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    t = Translator("ru")
    await callback.message.edit_text(
        t.t("admin_search_prompt"),
        reply_markup=admin_main_menu_keyboard(),
    )
    await state.set_state(AdminSearch.waiting_for_query)
    await callback.answer()


@router.message(AdminSearch.waiting_for_query)
async def on_admin_search_query(message: Message, state: FSMContext):
    """Handle search query."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    t = Translator("ru")
    query = message.text.strip()

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = await user_repo.search_users(query, limit=10)

    await state.clear()

    if not users:
        await message.answer(
            t.t("admin_search_no_results"),
            reply_markup=admin_main_menu_keyboard(),
        )
        return

    text = t.t("admin_users_list", page=1, total=1)
    await message.answer(
        text,
        reply_markup=admin_users_list_keyboard(users, page=0, total_pages=1),
    )


# =============================================================================
# User Detail
# =============================================================================

@router.callback_query(F.data.regexp(r"^admin:user:(\d+)$"))
async def on_admin_user_detail(callback: CallbackQuery):
    """Show user profile."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    await show_user_detail(callback.message, user_id)
    await callback.answer()


async def show_user_detail(message_or_callback, user_id: int):
    """Show detailed user profile."""
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)

        if not user:
            text = t.t("admin_user_not_found")
            if hasattr(message_or_callback, "edit_text"):
                await message_or_callback.edit_text(text, reply_markup=admin_main_menu_keyboard())
            else:
                await message_or_callback.answer(text, reply_markup=admin_main_menu_keyboard())
            return

        status = "🚫 Забанен" if user.is_banned else "✅ Активен"
        text = t.t(
            "admin_user_detail",
            telegram_id=user.telegram_id,
            username=user.username or "—",
            credits=user.credits,
            language=user.language.upper(),
            plan=user.subscription_type.upper(),
            referral_code=user.referral_code,
            created_at=user.created_at.strftime("%d.%m.%Y %H:%M"),
            status=status,
        )

    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.edit_text(
            text,
            reply_markup=admin_user_detail_keyboard(user.id, user.is_banned),
        )
    else:
        await message_or_callback.answer(
            text,
            reply_markup=admin_user_detail_keyboard(user.id, user.is_banned),
        )


# =============================================================================
# Credits Management
# =============================================================================

@router.callback_query(F.data.regexp(r"^admin:user:(\d+):(add|sub):(\d+)$"))
async def on_admin_user_credits(callback: CallbackQuery):
    """Add or remove credits from user."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])
    action = parts[3]
    amount = int(parts[4])

    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)

        if not user:
            await callback.answer(t.t("admin_user_not_found"), show_alert=True)
            return

        if action == "add":
            new_balance = await user_repo.add_credits(user_id, amount)
            await callback.answer(
                t.t("admin_credits_added", amount=amount, balance=new_balance),
                show_alert=True,
            )
        else:
            # Sub: deduct but not below 0
            success = await user_repo.deduct_credits(user_id, amount)
            if success:
                user = await user_repo.get_by_id(user_id)
                await callback.answer(
                    t.t("admin_credits_removed", amount=amount, balance=user.credits),
                    show_alert=True,
                )
            else:
                await callback.answer("❌ Недостаточно кредитов", show_alert=True)
                return

    # Refresh user detail view
    await show_user_detail(callback.message, user_id)


# =============================================================================
# Ban / Unban
# =============================================================================

@router.callback_query(F.data.regexp(r"^admin:user:(\d+):ban$"))
async def on_admin_user_ban(callback: CallbackQuery):
    """Ban user."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        await user_repo.set_banned(user_id, True)

    await callback.answer(t.t("admin_user_banned"), show_alert=True)
    await show_user_detail(callback.message, user_id)


@router.callback_query(F.data.regexp(r"^admin:user:(\d+):unban$"))
async def on_admin_user_unban(callback: CallbackQuery):
    """Unban user."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        await user_repo.set_banned(user_id, False)

    await callback.answer(t.t("admin_user_unbanned"), show_alert=True)
    await show_user_detail(callback.message, user_id)


# =============================================================================
# User Generation History
# =============================================================================

@router.callback_query(F.data.regexp(r"^admin:user:(\d+):history$"))
async def on_admin_user_history(callback: CallbackQuery):
    """Show user generation history."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_user_history(user_id=user_id, limit=20)

        if not generations:
            items = t.t("admin_history_empty")
        else:
            lines = []
            for gen in generations:
                status_icon = "✅" if gen.status == "completed" else "⏳" if gen.status == "pending" else "❌"
                style_name = gen.generation_type.replace("_", " ").title()
                lines.append(
                    f"{status_icon} <b>{gen.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
                    f"   🎨 {style_name} | 🤖 {gen.model_used} | 💰 {gen.credits_spent} cr\n"
                )
            items = "\n".join(lines)

    text = t.t("admin_user_history", items=items)
    await callback.message.edit_text(
        text,
        reply_markup=admin_user_history_keyboard(user_id),
    )
    await callback.answer()


# =============================================================================
# Generations (placeholder)
# =============================================================================

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


# =============================================================================
# Broadcast (placeholder)
# =============================================================================

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


# =============================================================================
# Back to admin dashboard
# =============================================================================

@router.callback_query(F.data == "admin:back")
async def on_admin_back(callback: CallbackQuery):
    """Return to admin dashboard."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    await show_dashboard(callback.message)
    await callback.answer()
