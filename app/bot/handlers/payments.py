"""
Telegram payment handlers.

Handles pre-checkout queries and successful payments for Telegram Stars.
Supports multilingual messages.
"""

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from app.bot.i18n import Translator
from app.bot.keyboards import main_menu_keyboard
from app.database import AsyncSessionLocal
from app.database.repositories import UserRepository
from app.payments.telegram_stars import process_successful_payment

logger = logging.getLogger(__name__)
router = Router()


async def get_user_language(telegram_id: int) -> str:
    """Fetch user's preferred language from database."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        return user.language if user else "en"


# =============================================================================
# Pre-Checkout Query
# =============================================================================

@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout: PreCheckoutQuery):
    """
    Answer pre-checkout query.

    Telegram requires bots to confirm they are ready to accept payment
    before the user is charged.
    """
    logger.info("Pre-checkout query from user %s: %s", pre_checkout.from_user.id, pre_checkout.invoice_payload)
    await pre_checkout.answer(ok=True)


# =============================================================================
# Successful Payment
# =============================================================================

@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    """
    Handle successful Telegram Stars payment.

    Credits are added to the user's account immediately.
    """
    lang = await get_user_language(message.from_user.id)
    t = Translator(lang)

    payment = message.successful_payment
    telegram_id = message.from_user.id

    logger.info(
        "Successful payment from user %s: %s, amount: %d %s",
        telegram_id,
        payment.invoice_payload,
        payment.total_amount,
        payment.currency,
    )

    try:
        result = await process_successful_payment(
            telegram_id=telegram_id,
            payload=payment.invoice_payload,
            total_amount=payment.total_amount,
            currency=payment.currency,
        )

        # Determine display name
        item_type = result["item_type"]
        item_name = result["item_name"]
        if item_type == "subscription":
            display_name = f"{item_name.title()} Plan"
        else:
            display_name = f"{item_name} Credits Pack"

        await message.answer(
            t.t("payment_success_stars",
                item_name=display_name,
                credits_added=result["credits_added"],
                new_balance=result["new_balance"]),
            reply_markup=main_menu_keyboard(lang),
        )

    except Exception as e:
        logger.exception("Error processing successful payment: %s", e)
        await message.answer(
            t.t("payment_failed"),
            reply_markup=main_menu_keyboard(lang),
        )
