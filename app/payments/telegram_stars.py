"""
Telegram Stars payment integration.

Uses aiogram's built-in payment methods to create invoices paid with Telegram Stars (XTR).
"""

import logging

from aiogram import Bot
from aiogram.types import LabeledPrice

from app.config import get_settings
from app.payments.credits import (
    CREDIT_PACKS,
    SUBSCRIPTION_PLANS,
    SUBSCRIPTION_PRICES,
    process_credit_pack_purchase,
    process_subscription_purchase,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# Invoice Creation
# =============================================================================

async def send_subscription_invoice(
    bot: Bot,
    chat_id: int,
    plan: str,  # "starter" or "pro"
) -> None:
    """
    Send a Telegram Stars invoice for a subscription plan.

    Args:
        bot: aiogram Bot instance
        chat_id: Telegram chat ID
        plan: Subscription plan key
    """
    plan_info = SUBSCRIPTION_PLANS.get(plan)
    prices = SUBSCRIPTION_PRICES.get(plan)
    if not plan_info or not prices:
        logger.error("Unknown plan for invoice: %s", plan)
        return

    title = f"{plan_info['name']} Plan"
    description = (
        f"{plan_info['credits']} credits/month\n"
        f"No watermark\n"
        f"AI Model: {plan_info['model']}\n"
        f"Priority: {plan_info['priority']}"
    )

    # Telegram Stars use currency "XTR" and amount in smallest units (1 star = 100)
    stars_amount = prices["stars"] * 100

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=f"subscription:{plan}",
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars_amount)],
        start_parameter=f"sub_{plan}",
    )
    logger.info("Sent subscription invoice: %s to chat %s for %d stars", plan, chat_id, prices["stars"])


async def send_credit_pack_invoice(
    bot: Bot,
    chat_id: int,
    pack_size: str,  # "50", "100", "500"
) -> None:
    """
    Send a Telegram Stars invoice for a credit pack.

    Args:
        bot: aiogram Bot instance
        chat_id: Telegram chat ID
        pack_size: Credit pack size
    """
    pack = CREDIT_PACKS.get(pack_size)
    if not pack:
        logger.error("Unknown credit pack for invoice: %s", pack_size)
        return

    title = f"{pack['credits']} Credits Pack"
    description = f"One-time purchase of {pack['credits']} generation credits."
    stars_amount = pack["price_stars"] * 100

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=f"pack:{pack_size}",
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars_amount)],
        start_parameter=f"pack_{pack_size}",
    )
    logger.info("Sent credit pack invoice: %s to chat %s for %d stars", pack_size, chat_id, pack["price_stars"])


# =============================================================================
# Payment Processing
# =============================================================================

async def process_successful_payment(
    telegram_id: int,
    payload: str,
    total_amount: int,
    currency: str,
) -> dict:
    """
    Process a successful Telegram Stars payment.

    Args:
        telegram_id: Telegram user ID
        payload: Invoice payload (e.g., "subscription:starter" or "pack:50")
        total_amount: Amount paid (in smallest currency units)
        currency: Currency code ("XTR" for Stars)

    Returns:
        Dict with purchase result
    """
    from app.database import AsyncSessionLocal
    from app.database.repositories import UserRepository

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError(f"User not found: {telegram_id}")

    parts = payload.split(":")
    item_type = parts[0]
    item_name = parts[1]

    result = {
        "user_id": user.id,
        "telegram_id": telegram_id,
        "item_type": item_type,
        "item_name": item_name,
        "amount_paid": total_amount / 100,  # Convert back to stars
        "currency": currency,
    }

    if item_type == "subscription":
        purchase_result = await process_subscription_purchase(user.id, item_name)
        result.update(purchase_result)
        logger.info("Processed subscription payment: %s for user %d", item_name, user.id)

    elif item_type == "pack":
        purchase_result = await process_credit_pack_purchase(user.id, item_name)
        result.update(purchase_result)
        logger.info("Processed credit pack payment: %s for user %d", item_name, user.id)

    else:
        raise ValueError(f"Unknown payment payload: {payload}")

    return result
