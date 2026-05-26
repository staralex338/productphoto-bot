"""
Credit and subscription management.

Handles adding credits, setting subscriptions, and defining pricing.
"""

import logging

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import UserRepository

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# Pricing Definitions
# =============================================================================

SUBSCRIPTION_PLANS = {
    "starter": {
        "name": "Starter",
        "credits": 100,
        "monthly": True,
        "watermark": False,
        "model": "flux_schnell",
        "priority": "normal",
    },
    "pro": {
        "name": "Pro",
        "credits": 500,
        "monthly": True,
        "watermark": False,
        "model": "flux_dev",
        "priority": "high",
    },
}

CREDIT_PACKS = {
    "50": {"credits": 50, "price_stars": 100, "price_usd_cents": 499},
    "100": {"credits": 100, "price_stars": 180, "price_usd_cents": 899},
    "500": {"credits": 500, "price_stars": 800, "price_usd_cents": 3999},
}

SUBSCRIPTION_PRICES = {
    "starter": {"stars": 300, "usd_cents": 1499},
    "pro": {"stars": 1200, "usd_cents": 4999},
}


# =============================================================================
# Credit Operations
# =============================================================================

async def add_credits_to_user(user_id: int, amount: int, source: str = "purchase") -> int:
    """
    Add credits to a user's account.

    Args:
        user_id: Database user ID
        amount: Number of credits to add
        source: Reason for adding credits (for logging)

    Returns:
        New credit balance
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        new_balance = await user_repo.add_credits(user_id, amount)
        logger.info("Added %d credits to user %d (source: %s). New balance: %d", amount, user_id, source, new_balance)
        return new_balance


async def process_subscription_purchase(user_id: int, plan: str) -> dict:
    """
    Process a subscription purchase.

    Sets subscription type and adds monthly credits.

    Args:
        user_id: Database user ID
        plan: "starter" or "pro"

    Returns:
        Dict with plan details
    """
    plan_info = SUBSCRIPTION_PLANS.get(plan)
    if not plan_info:
        raise ValueError(f"Unknown plan: {plan}")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        await user_repo.set_subscription(user_id, plan)
        new_balance = await user_repo.add_credits(user_id, plan_info["credits"])

    logger.info("User %d subscribed to %s plan. Credits added: %d", user_id, plan, plan_info["credits"])

    return {
        "plan": plan,
        "credits_added": plan_info["credits"],
        "new_balance": new_balance,
        "monthly": plan_info["monthly"],
    }


async def process_credit_pack_purchase(user_id: int, pack_size: str) -> dict:
    """
    Process a one-time credit pack purchase.

    Args:
        user_id: Database user ID
        pack_size: "50", "100", or "500"

    Returns:
        Dict with pack details
    """
    pack = CREDIT_PACKS.get(pack_size)
    if not pack:
        raise ValueError(f"Unknown credit pack: {pack_size}")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        new_balance = await user_repo.add_credits(user_id, pack["credits"])

    logger.info("User %d bought %s credit pack. Credits added: %d", user_id, pack_size, pack["credits"])

    return {
        "pack_size": pack_size,
        "credits_added": pack["credits"],
        "new_balance": new_balance,
    }


def get_price_display(item_type: str, item_name: str, currency: str = "stars") -> str:
    """Get human-readable price for display."""
    if item_type == "subscription":
        prices = SUBSCRIPTION_PRICES.get(item_name, {})
        amount = prices.get(currency, 0)
        if currency == "stars":
            return f"⭐ {amount} Stars/month"
        else:
            return f"${amount / 100:.2f}/month"
    elif item_type == "pack":
        pack = CREDIT_PACKS.get(item_name, {})
        amount = pack.get("price_stars" if currency == "stars" else "price_usd_cents", 0)
        if currency == "stars":
            return f"⭐ {amount} Stars"
        else:
            return f"${amount / 100:.2f}"
    return "N/A"
