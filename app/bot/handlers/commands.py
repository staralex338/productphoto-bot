"""
Command handlers for Telegram bot.

Handles /start, /help, /balance, /history commands.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    buy_credits_keyboard,
    main_menu_keyboard,
    referral_keyboard,
)
from app.bot.messages import (
    BALANCE_MESSAGE,
    HELP_MESSAGE,
    HISTORY_EMPTY_MESSAGE,
    REFERRAL_MESSAGE,
    WELCOME_MESSAGE,
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

    If user arrives with a referral code (e.g., /start REFCODE),
    process it after user creation.
    """
    args = message.text.split(maxsplit=1)[1:] if message.text else []
    referral_code = args[0].upper() if args else None

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        # Process referral code if provided and user is new (has default credits)
        if referral_code:
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
                # Send bonus notification to new user
                await message.answer(
                    f"🎉 <b>Welcome bonus!</b>\n\n"
                    f"You were invited by a friend and received "
                    f"<b>+{result['bonus_invited']}</b> bonus credits!\n\n"
                    f"Your friend also got <b>+{result['bonus_inviter']}</b> credits. 🎁",
                )
            except SelfReferralError:
                logger.info("User %d tried to self-refer", message.from_user.id)
            except AlreadyReferredError:
                logger.info("User %d already referred", message.from_user.id)
            except InvalidReferralCodeError:
                logger.info("Invalid referral code: %s", referral_code)
            except Exception as e:
                logger.exception("Referral processing error: %s", e)

        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=main_menu_keyboard(),
        )


# =============================================================================
# /help
# =============================================================================

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(HELP_MESSAGE, reply_markup=main_menu_keyboard())


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
            await message.answer("Please send /start first.")
            return

        text = BALANCE_MESSAGE.format(
            credits=user.credits,
            plan=user.subscription_type.upper(),
            referral_code=user.referral_code,
            referral_bonus=settings.referral_bonus_inviter,
        )
        await message.answer(text, reply_markup=buy_credits_keyboard())


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
            await message.answer("Please send /start first.")
            return

        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_user_history(user_id=user.id, limit=10)

        if not generations:
            await message.answer(
                HISTORY_EMPTY_MESSAGE,
                reply_markup=main_menu_keyboard(),
            )
            return

        # Build history text with more details
        lines = ["📜 <b>Your Last Generations</b>\n"]
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
            reply_markup=main_menu_keyboard(),
        )


# =============================================================================
# Menu Callbacks (routing to commands or direct handlers)
# =============================================================================

@router.callback_query(F.data == "menu:main")
async def on_menu_main(callback: CallbackQuery):
    """Return to main menu."""
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def on_menu_help(callback: CallbackQuery):
    """Show help from menu button."""
    await callback.message.edit_text(
        HELP_MESSAGE,
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def on_menu_profile(callback: CallbackQuery):
    """Show profile from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("User not found. Send /start", show_alert=True)
            return

        text = BALANCE_MESSAGE.format(
            credits=user.credits,
            plan=user.subscription_type.upper(),
            referral_code=user.referral_code,
            referral_bonus=settings.referral_bonus_inviter,
        )
        await callback.message.edit_text(text, reply_markup=buy_credits_keyboard())
        await callback.answer()


@router.callback_query(F.data == "menu:history")
async def on_menu_history(callback: CallbackQuery):
    """Show history from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("User not found. Send /start", show_alert=True)
            return

        gen_repo = GenerationRepository(session)
        generations = await gen_repo.get_user_history(user_id=user.id, limit=10)

        if not generations:
            await callback.message.edit_text(
                HISTORY_EMPTY_MESSAGE,
                reply_markup=main_menu_keyboard(),
            )
            await callback.answer()
            return

        lines = ["📜 <b>Your Last Generations</b>\n"]
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
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()


@router.callback_query(F.data == "menu:referral")
async def on_menu_referral(callback: CallbackQuery, bot: Bot):
    """Show referral info from menu button."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("User not found. Send /start", show_alert=True)
            return

        # Get actual referral stats
        from app.bot.services.referrals import get_referral_stats
        stats = await get_referral_stats(user.id)

        # Get bot username for referral link
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"

        text = REFERRAL_MESSAGE.format(
            inviter_bonus=settings.referral_bonus_inviter,
            invited_bonus=settings.referral_bonus_invited,
            referral_link=referral_link,
            total_invited=stats["total_invited"],
            credits_earned=stats["credits_earned"],
        )
        await callback.message.edit_text(
            text,
            reply_markup=referral_keyboard(referral_link),
        )
        await callback.answer()
