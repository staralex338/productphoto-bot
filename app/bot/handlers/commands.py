"""
Command handlers for Telegram bot.

Handles /start, /help, /balance, /history commands.
Supports language selection for new users.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import Translator
from app.bot.keyboards import (
    buy_credits_keyboard,
    language_selection_keyboard,
    main_menu_keyboard,
    referral_keyboard,
)
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import GenerationRepository, UserRepository

logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


async def get_db_session() -> AsyncSession:
    """Factory to create a new DB session for handlers."""
    async with AsyncSessionLocal() as session:
        return session


# =============================================================================
# /start
# =============================================================================

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Handle /start command.

    If user is new — show language selection.
    If existing — show main menu in their language.
    """
    args = message.text.split(maxsplit=1)[1:] if message.text else []
    referral_code = args[0].upper() if args else None

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user, is_new = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        logger.info("cmd_start: user_id=%s is_new=%s language=%s", 
                    message.from_user.id, is_new, user.language)

        # Process referral code if provided and user is new
        if referral_code and is_new:
            from app.bot.services.referrals import (
                AlreadyReferredError,
                InvalidReferralCodeError,
                SelfReferralError,
                process_referral,
            )

            try:
                result = await process_referral(
                    new_user_telegram_id=message.from_user.id,
                    referral_code=referral_code,
                )
                t = Translator(user.language)
                await message.answer(
                    t.t("referral_bonus",
                        bonus_invited=result['bonus_invited'],
                        bonus_inviter=result['bonus_inviter']),
                )
            except SelfReferralError:
                logger.info("User %d tried to self-refer", message.from_user.id)
            except AlreadyReferredError:
                logger.info("User %d already referred", message.from_user.id)
            except InvalidReferralCodeError:
                logger.info("Invalid referral code: %s", referral_code)
            except Exception as e:
                logger.exception("Referral processing error: %s", e)

        if is_new:
            # New user — show language selection
            await message.answer(
                "🌍 <b>Choose your language / Выберите язык</b>",
                reply_markup=language_selection_keyboard(),
            )
        else:
            # Existing user — show main menu in their language
            t = Translator(user.language)
            await message.answer(
                t.t("welcome",
                    app_name=settings.app_name,
                    free_credits=settings.free_credits_on_start),
                reply_markup=main_menu_keyboard(user.language),
            )


# =============================================================================
# Language Selection Callback
# =============================================================================

@router.callback_query(F.data.startswith("lang:"))
async def on_language_selected(callback: CallbackQuery):
    """Handle language selection from new user."""
    lang = callback.data.split(":")[1]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if user:
            await user_repo.set_language(user.id, lang)

        t = Translator(lang)
        await callback.message.edit_text(
            t.t("welcome",
                app_name=settings.app_name,
                free_credits=settings.free_credits_on_start),
            reply_markup=main_menu_keyboard(lang),
        )
        await callback.answer()


# =============================================================================
# /lang — Change language
# =============================================================================

@router.message(Command("lang"))
async def cmd_lang(message: Message):
    """Allow user to change language at any time."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer(Translator("en").t("please_start"))
            return

    await message.answer(
        "🌍 <b>Choose your language / Выберите язык</b>",
        reply_markup=language_selection_keyboard(),
    )


# =============================================================================
# /help
# =============================================================================

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        lang = user.language if user else "en"

    t = Translator(lang)
    await message.answer(
        t.t("help",
            app_name=settings.app_name,
            max_size=settings.max_image_size_mb,
            min_dim=settings.min_image_dimension),
        reply_markup=main_menu_keyboard(lang),
    )


# =============================================================================
# /balance
# =============================================================================

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Handle /balance command — show user profile and credits."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer(Translator("en").t("please_start"))
            return

        t = Translator(user.language)
        text = t.t("balance",
            credits=user.credits,
            plan=user.subscription_type.upper(),
            referral_code=user.referral_code,
            referral_bonus=settings.referral_bonus_inviter,
        )
        await message.answer(text, reply_markup=buy_credits_keyboard(user.language))


# =============================================================================
# /history
# =============================================================================

@router.message(Command("history"))
async def cmd_history(message: Message):
    """Handle /history command — show past generations."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer(Translator("en").t("please_start"))
            return

        t = Translator(user.language)
        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_user_history(user_id=user.id, limit=10)

        if not generations:
            await message.answer(
                t.t("history_empty"),
                reply_markup=main_menu_keyboard(user.language),
            )
            return

        # Build history text with more details
        lines = [t.t("history_title")]
        for gen in generations:
            status_icon = "✅" if gen.status == "completed" else "⏳" if gen.status == "pending" else "❌"
            style_name = gen.generation_type.replace('_', ' ').title()
            lines.append(
                f"{status_icon} <b>{gen.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"   🎨 {style_name}\n"
                f"   🤖 {gen.model_used}\n"
                f"   💰 {gen.credits_spent} credit(s)\n"
            )

        await message.answer(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(user.language),
        )


# =============================================================================
# Menu Callbacks (routing to commands or direct handlers)
# =============================================================================

@router.callback_query(F.data == "menu:main")
async def on_menu_main(callback: CallbackQuery):
    """Return to main menu."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        lang = user.language if user else "en"

    t = Translator(lang)
    await callback.message.edit_text(
        t.t("welcome",
            app_name=settings.app_name,
            free_credits=settings.free_credits_on_start),
        reply_markup=main_menu_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def on_menu_language(callback: CallbackQuery):
    """Show language selection from menu button."""
    await callback.message.edit_text(
        "🌍 <b>Choose your language / Выберите язык</b>",
        reply_markup=language_selection_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def on_menu_help(callback: CallbackQuery):
    """Show help from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        lang = user.language if user else "en"

    t = Translator(lang)
    await callback.message.edit_text(
        t.t("help",
            app_name=settings.app_name,
            max_size=settings.max_image_size_mb,
            min_dim=settings.min_image_dimension),
        reply_markup=main_menu_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def on_menu_profile(callback: CallbackQuery):
    """Show profile from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer(Translator("en").t("user_not_found"), show_alert=True)
            return

        t = Translator(user.language)
        text = t.t("balance",
            credits=user.credits,
            plan=user.subscription_type.upper(),
            referral_code=user.referral_code,
            referral_bonus=settings.referral_bonus_inviter,
        )
        await callback.message.edit_text(text, reply_markup=buy_credits_keyboard(user.language))
        await callback.answer()


@router.callback_query(F.data == "menu:history")
async def on_menu_history(callback: CallbackQuery):
    """Show history from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer(Translator("en").t("user_not_found"), show_alert=True)
            return

        t = Translator(user.language)
        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_user_history(user_id=user.id, limit=10)

        if not generations:
            await callback.message.edit_text(
                t.t("history_empty"),
                reply_markup=main_menu_keyboard(user.language),
            )
            await callback.answer()
            return

        lines = [t.t("history_title")]
        for gen in generations:
            status_icon = "✅" if gen.status == "completed" else "⏳" if gen.status == "pending" else "❌"
            style_name = gen.generation_type.replace('_', ' ').title()
            lines.append(
                f"{status_icon} <b>{gen.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"   🎨 {style_name}\n"
                f"   🤖 {gen.model_used}\n"
                f"   💰 {gen.credits_spent} credit(s)\n"
            )

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(user.language),
        )
        await callback.answer()


@router.callback_query(F.data == "menu:referral")
async def on_menu_referral(callback: CallbackQuery, bot: Bot):
    """Show referral info from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer(Translator("en").t("user_not_found"), show_alert=True)
            return

        # Get actual referral stats
        from app.bot.services.referrals import get_referral_stats
        stats = await get_referral_stats(user.id)

        # Get bot username for referral link
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"

        t = Translator(user.language)
        text = t.t("referral",
            inviter_bonus=settings.referral_bonus_inviter,
            invited_bonus=settings.referral_bonus_invited,
            referral_link=referral_link,
            total_invited=stats["total_invited"],
            credits_earned=stats["credits_earned"],
        )
        await callback.message.edit_text(
            text,
            reply_markup=referral_keyboard(referral_link, user.language),
        )
        await callback.answer()
