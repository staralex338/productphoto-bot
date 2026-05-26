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
    admin_broadcast_confirm_keyboard,
    admin_broadcast_menu_keyboard,
    admin_dashboard_keyboard,
    admin_finances_menu_keyboard,
    admin_generation_detail_keyboard,
    admin_generations_list_keyboard,
    admin_generations_menu_keyboard,
    admin_main_menu_keyboard,
    admin_settings_menu_keyboard,
    admin_settings_value_keyboard,
    admin_user_detail_keyboard,
    admin_user_history_keyboard,
    admin_users_list_keyboard,
)
from app.bot.states import AdminBroadcast, AdminSearch, AdminSettings
from app.database import AsyncSessionLocal
from app.database.repositories import (
    GenerationRepository,
    PaymentRepository,
    SettingsRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)
router = Router()

# Admin Telegram ID
ADMIN_TELEGRAM_ID = 1003330009
USERS_PER_PAGE = 10
GEN_PER_PAGE = 10


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
        return

    await show_dashboard(message)


# =============================================================================
# Dashboard
# =============================================================================

async def show_dashboard(message_or_callback):
    """Build and send admin dashboard."""
    t = Translator("ru")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        gen_repo = GenerationRepository(session)
        payment_repo = PaymentRepository(session)

        total_users = await user_repo.get_total_users()
        new_today = await user_repo.get_new_users_count(today_start)
        new_week = await user_repo.get_new_users_count(week_start)
        new_month = await user_repo.get_new_users_count(month_start)

        total_generations = await gen_repo.get_total_generations()
        gen_today = await gen_repo.get_generations_count(today_start)

        total_revenue = await payment_repo.get_total_revenue()
        revenue_today = await payment_repo.get_revenue(today_start)

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
        await message_or_callback.edit_text(text, reply_markup=admin_dashboard_keyboard())
    else:
        await message_or_callback.answer(text, reply_markup=admin_dashboard_keyboard())


@router.callback_query(F.data == "admin:dashboard")
async def on_admin_dashboard(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    await show_dashboard(callback.message)
    await callback.answer("🔄 Обновлено")


# =============================================================================
# Users
# =============================================================================

@router.callback_query(F.data == "admin:users")
async def on_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    await show_users_page(callback.message, page=0)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:users:(\d+)$"))
async def on_admin_users_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    page = int(callback.data.split(":")[2])
    await show_users_page(callback.message, page=page)
    await callback.answer()


async def show_users_page(message_or_callback, page: int = 0):
    t = Translator("ru")
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        total_users = await user_repo.get_total_users()
        total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
        users = await user_repo.get_users_paginated(offset=page * USERS_PER_PAGE, limit=USERS_PER_PAGE)

    if not users:
        text = t.t("admin_users_list", page=1, total=1) + "\n\n<i>Пользователей пока нет</i>"
    else:
        text = t.t("admin_users_list", page=page + 1, total=total_pages)

    markup = admin_users_list_keyboard(users, page, total_pages)
    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.edit_text(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


@router.callback_query(F.data == "admin:users:search")
async def on_admin_users_search(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_search_prompt"), reply_markup=admin_main_menu_keyboard())
    await state.set_state(AdminSearch.waiting_for_query)
    await callback.answer()


@router.message(AdminSearch.waiting_for_query)
async def on_admin_search_query(message: Message, state: FSMContext):
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
        await message.answer(t.t("admin_search_no_results"), reply_markup=admin_main_menu_keyboard())
        return

    await message.answer(
        t.t("admin_users_list", page=1, total=1),
        reply_markup=admin_users_list_keyboard(users, page=0, total_pages=1),
    )


@router.callback_query(F.data.regexp(r"^admin:user:(\d+)$"))
async def on_admin_user_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    user_id = int(callback.data.split(":")[2])
    await show_user_detail(callback.message, user_id)
    await callback.answer()


async def show_user_detail(message_or_callback, user_id: int):
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
        await message_or_callback.edit_text(text, reply_markup=admin_user_detail_keyboard(user.id, user.is_banned))
    else:
        await message_or_callback.answer(text, reply_markup=admin_user_detail_keyboard(user.id, user.is_banned))


@router.callback_query(F.data.regexp(r"^admin:user:(\d+):(add|sub):(\d+)$"))
async def on_admin_user_credits(callback: CallbackQuery):
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
            await callback.answer(t.t("admin_credits_added", amount=amount, balance=new_balance), show_alert=True)
        else:
            success = await user_repo.deduct_credits(user_id, amount)
            if success:
                user = await user_repo.get_by_id(user_id)
                await callback.answer(t.t("admin_credits_removed", amount=amount, balance=user.credits), show_alert=True)
            else:
                await callback.answer("❌ Недостаточно кредитов", show_alert=True)
                return

    await show_user_detail(callback.message, user_id)


@router.callback_query(F.data.regexp(r"^admin:user:(\d+):ban$"))
async def on_admin_user_ban(callback: CallbackQuery):
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


@router.callback_query(F.data.regexp(r"^admin:user:(\d+):history$"))
async def on_admin_user_history(callback: CallbackQuery):
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

    await callback.message.edit_text(
        t.t("admin_user_history", items=items),
        reply_markup=admin_user_history_keyboard(user_id),
    )
    await callback.answer()


# =============================================================================
# Generations
# =============================================================================

@router.callback_query(F.data == "admin:generations")
async def on_admin_generations(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_gen_menu"), reply_markup=admin_generations_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:gen:styles")
async def on_admin_gen_styles(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        gen_repo = GenerationRepository(session)
        stats = await gen_repo.get_style_stats()

    if not stats:
        lines = ["<i>Пока нет данных</i>"]
    else:
        lines = []
        for style, count in stats:
            style_name = style.replace("_", " ").title()
            lines.append(f"🎨 {style_name}: <b>{count}</b>")

    await callback.message.edit_text(
        t.t("admin_gen_styles", stats="\n".join(lines)),
        reply_markup=admin_generations_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:gen:(pending|completed|failed)$"))
async def on_admin_gen_filter(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    status = callback.data.split(":")[2]
    await show_generations_list(callback.message, status, page=0)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:gen:(pending|completed|failed):(\d+)$"))
async def on_admin_gen_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    parts = callback.data.split(":")
    status = parts[2]
    page = int(parts[3])
    await show_generations_list(callback.message, status, page)
    await callback.answer()


async def show_generations_list(message_or_callback, status: str, page: int = 0):
    t = Translator("ru")
    async with AsyncSessionLocal() as session:
        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_generations_by_status(status, limit=100)
        total_pages = max(1, (len(generations) + GEN_PER_PAGE - 1) // GEN_PER_PAGE)
        start = page * GEN_PER_PAGE
        end = start + GEN_PER_PAGE
        page_gens = generations[start:end]

    text = t.t("admin_gen_list", filter=status.upper())
    markup = admin_generations_list_keyboard(page_gens, status, page, total_pages)
    if hasattr(message_or_callback, "edit_text"):
        await message_or_callback.edit_text(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


@router.callback_query(F.data.regexp(r"^admin:gen:(\d+)$"))
async def on_admin_gen_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    gen_id = int(callback.data.split(":")[2])
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        gen_repo = GenerationRepository(session)
        gen = await gen_repo.get_by_id(gen_id)

    if not gen:
        await callback.answer("Generation not found", show_alert=True)
        return

    status_icon = "✅" if gen.status == "completed" else "⏳" if gen.status == "pending" else "❌"
    text = t.t(
        "admin_gen_detail",
        id=gen.id,
        user_id=gen.user_id,
        style=gen.generation_type.replace("_", " ").title(),
        model=gen.model_used,
        status=status_icon,
        credits=gen.credits_spent,
        created_at=gen.created_at.strftime("%d.%m.%Y %H:%M"),
        error=gen.error_message or "—",
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_generation_detail_keyboard(gen.id, can_retry=(gen.status == "failed")),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:gen:(\d+):retry$"))
async def on_admin_gen_retry(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    gen_id = int(callback.data.split(":")[2])
    t = Translator("ru")

    # TODO: Implement actual retry logic
    await callback.answer(t.t("admin_gen_retried", id=gen_id), show_alert=True)


# =============================================================================
# Finances
# =============================================================================

@router.callback_query(F.data == "admin:fin")
async def on_admin_finances(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_fin_menu"), reply_markup=admin_finances_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:fin:payments")
async def on_admin_fin_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        payment_repo = PaymentRepository(session)
        payments = await payment_repo.get_payments_paginated(limit=20)

    if not payments:
        items = "<i>Платежей пока нет</i>"
    else:
        lines = []
        for p in payments:
            icon = "✅" if p.status == "completed" else "⏳" if p.status == "pending" else "❌"
            lines.append(
                f"{icon} <b>#{p.id}</b> | {p.provider} | ${p.amount}\n"
                f"   📦 {p.plan_name or p.payment_type} | 📆 {p.created_at.strftime('%d.%m.%Y')}\n"
            )
        items = "\n".join(lines)

    await callback.message.edit_text(
        t.t("admin_fin_payments", items=items),
        reply_markup=admin_finances_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:fin:stars")
async def on_admin_fin_stars(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        payment_repo = PaymentRepository(session)
        payments = await payment_repo.get_payments_by_provider("telegram_stars", limit=20)

    if not payments:
        items = "<i>Платежей Stars пока нет</i>"
    else:
        lines = []
        for p in payments:
            icon = "✅" if p.status == "completed" else "❌"
            lines.append(
                f"{icon} <b>#{p.id}</b> | ⭐ {p.amount} stars | 📆 {p.created_at.strftime('%d.%m.%Y')}\n"
            )
        items = "\n".join(lines)

    await callback.message.edit_text(
        t.t("admin_fin_payments", items=items),
        reply_markup=admin_finances_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:fin:stripe")
async def on_admin_fin_stripe(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        payment_repo = PaymentRepository(session)
        payments = await payment_repo.get_payments_by_provider("stripe", limit=20)

    if not payments:
        items = "<i>Платежей Stripe пока нет</i>"
    else:
        lines = []
        for p in payments:
            icon = "✅" if p.status == "completed" else "❌"
            lines.append(
                f"{icon} <b>#{p.id}</b> | 💳 ${p.amount} | 📆 {p.created_at.strftime('%d.%m.%Y')}\n"
            )
        items = "\n".join(lines)

    await callback.message.edit_text(
        t.t("admin_fin_payments", items=items),
        reply_markup=admin_finances_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:fin:plans")
async def on_admin_fin_plans(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        payment_repo = PaymentRepository(session)
        stats = await payment_repo.get_popular_plans()

    if not stats:
        lines = ["<i>Пока нет данных</i>"]
    else:
        lines = []
        for plan, count in stats:
            plan_name = (plan or "Unknown").replace("_", " ").title()
            lines.append(f"📦 {plan_name}: <b>{count}</b>")

    await callback.message.edit_text(
        t.t("admin_fin_plans", stats="\n".join(lines)),
        reply_markup=admin_finances_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:fin:refunds")
async def on_admin_fin_refunds(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")

    async with AsyncSessionLocal() as session:
        payment_repo = PaymentRepository(session)
        count = await payment_repo.get_refunds_count()

    await callback.message.edit_text(
        t.t("admin_fin_refunds", count=count),
        reply_markup=admin_finances_menu_keyboard(),
    )
    await callback.answer()


# =============================================================================
# Broadcast
# =============================================================================

@router.callback_query(F.data == "admin:broadcast")
async def on_admin_broadcast(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_bc_menu"), reply_markup=admin_broadcast_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:bc:(all|lang:\w+|plan:\w+)$"))
async def on_admin_broadcast_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    target = callback.data.split(":", 2)[2]
    await state.update_data(bc_target=target)

    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_bc_prompt"), reply_markup=admin_main_menu_keyboard())
    await state.set_state(AdminBroadcast.waiting_for_message)
    await callback.answer()


@router.message(AdminBroadcast.waiting_for_message)
async def on_admin_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    # Store message content
    if message.text:
        content = message.text
        content_type = "text"
    else:
        await message.answer("Пока поддерживается только текст. Отправьте текстовое сообщение.")
        return

    data = await state.get_data()
    target = data.get("bc_target", "all")

    # Count recipients
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        if target == "all":
            recipients = await user_repo.get_total_users()
        elif target.startswith("lang:"):
            # TODO: add filter by language
            recipients = await user_repo.get_total_users()
        elif target.startswith("plan:"):
            # TODO: add filter by plan
            recipients = await user_repo.get_total_users()
        else:
            recipients = 0

    await state.update_data(bc_message=content, bc_recipients=recipients)

    t = Translator("ru")
    preview = t.t("admin_bc_preview", message=content[:500], count=recipients)
    await message.answer(preview, reply_markup=admin_broadcast_confirm_keyboard())
    await state.set_state(AdminBroadcast.waiting_for_confirmation)


@router.callback_query(F.data == "admin:bc:confirm", AdminBroadcast.waiting_for_confirmation)
async def on_admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    data = await state.get_data()
    message_text = data.get("bc_message", "")
    target = data.get("bc_target", "all")

    t = Translator("ru")

    # Get users to send to
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        # For now, send to all non-banned users
        # TODO: implement filtering by language/plan
        users = await user_repo.get_users_paginated(offset=0, limit=10000)

    sent = 0
    failed = 0
    for user in users:
        if user.is_banned:
            continue
        try:
            await callback.bot.send_message(chat_id=user.telegram_id, text=message_text)
            sent += 1
        except Exception:
            failed += 1

    await callback.message.edit_text(
        t.t("admin_bc_sent", sent=sent, total=sent + failed),
        reply_markup=admin_main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()


# =============================================================================
# Settings
# =============================================================================

@router.callback_query(F.data == "admin:settings")
async def on_admin_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    t = Translator("ru")
    await callback.message.edit_text(t.t("admin_set_menu"), reply_markup=admin_settings_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:set:(prices|bonus|gen|wm)$"))
async def on_admin_setting_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return

    setting_key = callback.data.split(":")[2]
    setting_names = {
        "prices": "Цены на кредиты",
        "bonus": "Стартовый бонус",
        "gen": "Генерация (on/off)",
        "wm": "Watermark",
    }
    setting_name = setting_names.get(setting_key, setting_key)

    # Get current value from DB or default
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        current = await settings_repo.get(f"admin_{setting_key}", default="not set")

    t = Translator("ru")
    await state.update_data(setting_key=setting_key, setting_name=setting_name)
    await callback.message.edit_text(
        t.t("admin_set_prompt", name=setting_name, current=current),
        reply_markup=admin_settings_value_keyboard(setting_key),
    )
    await state.set_state(AdminSettings.waiting_for_value)
    await callback.answer()


@router.message(AdminSettings.waiting_for_value)
async def on_admin_setting_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    setting_key = data.get("setting_key")
    setting_name = data.get("setting_name")
    value = message.text.strip()

    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set(f"admin_{setting_key}", value, description=setting_name)

    t = Translator("ru")
    await message.answer(
        t.t("admin_set_updated", name=setting_name, value=value),
        reply_markup=admin_settings_menu_keyboard(),
    )
    await state.clear()


# =============================================================================
# Back handlers
# =============================================================================

@router.callback_query(F.data == "admin:back")
async def on_admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    await show_dashboard(callback.message)
    await callback.answer()
