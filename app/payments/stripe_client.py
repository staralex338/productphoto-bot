"""
Stripe payment integration.

Uses Stripe Checkout Sessions for one-time purchases and subscriptions.
Webhooks handle successful payments asynchronously.
"""

import logging

import stripe

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import PaymentRepository, UserRepository
from app.models.payment import Payment
from app.payments.credits import (
    CREDIT_PACKS,
    SUBSCRIPTION_PRICES,
    process_credit_pack_purchase,
    process_subscription_purchase,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe client
stripe.api_key = settings.stripe_secret_key


# =============================================================================
# Checkout Sessions
# =============================================================================

async def create_credit_pack_session(
    telegram_id: int,
    pack_size: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """
    Create a Stripe Checkout Session for a credit pack.

    Args:
        telegram_id: Telegram user ID (stored in metadata)
        pack_size: "50", "100", or "500"
        success_url: Redirect URL after successful payment
        cancel_url: Redirect URL after cancelled payment

    Returns:
        Checkout session URL
    """
    pack = CREDIT_PACKS.get(pack_size)
    if not pack:
        raise ValueError(f"Unknown pack: {pack_size}")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{pack['credits']} Credits Pack",
                        "description": f"One-time purchase of {pack['credits']} AI generation credits",
                    },
                    "unit_amount": pack["price_usd_cents"],
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "telegram_id": str(telegram_id),
            "item_type": "pack",
            "item_name": pack_size,
        },
    )

    logger.info("Created Stripe checkout session %s for pack %s", session.id, pack_size)
    return session.url


async def create_subscription_session(
    telegram_id: int,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """
    Create a Stripe Checkout Session for a subscription.

    Args:
        telegram_id: Telegram user ID
        plan: "starter" or "pro"
        success_url: Redirect URL after successful payment
        cancel_url: Redirect URL after cancelled payment

    Returns:
        Checkout session URL
    """
    prices = SUBSCRIPTION_PRICES.get(plan)
    if not prices:
        raise ValueError(f"Unknown plan: {plan}")

    # For MVP, we treat subscriptions as one-time payments with credit allocation
    # In production, create Stripe Products/Prices and use mode="subscription"
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{plan.title()} Plan",
                        "description": f"Monthly subscription with {SUBSCRIPTION_PLANS[plan]['credits']} credits",
                    },
                    "unit_amount": prices["usd_cents"],
                    # For true subscriptions, use recurring interval here
                    # "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }
        ],
        mode="payment",  # Use "subscription" with Stripe Prices in production
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "telegram_id": str(telegram_id),
            "item_type": "subscription",
            "item_name": plan,
        },
    )

    logger.info("Created Stripe checkout session %s for plan %s", session.id, plan)
    return session.url


# =============================================================================
# Webhook Processing
# =============================================================================

async def handle_stripe_webhook(payload: bytes, signature: str) -> dict:
    """
    Process Stripe webhook events.

    Args:
        payload: Raw request body
        signature: Stripe-Signature header

    Returns:
        Dict with processing result
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid signature")

    logger.info("Stripe webhook received: %s", event["type"])

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        return await _process_checkout_session(session)

    return {"status": "ignored", "event": event["type"]}


async def _process_checkout_session(session: dict) -> dict:
    """Process a completed checkout session."""
    metadata = session.get("metadata", {})
    telegram_id = int(metadata.get("telegram_id", 0))
    item_type = metadata.get("item_type")
    item_name = metadata.get("item_name")

    if not telegram_id or not item_type or not item_name:
        logger.error("Missing metadata in Stripe session: %s", session.get("id"))
        return {"status": "error", "reason": "missing_metadata"}

    # Prevent duplicate processing
    payment_id = session.get("payment_intent") or session.get("id")
    async with AsyncSessionLocal() as db_session:
        # Check if already processed
        existing = await db_session.execute(
            select(Payment).where(Payment.provider_payment_id == payment_id)
        )
        if existing.scalar_one_or_none():
            logger.info("Payment %s already processed, skipping", payment_id)
            return {"status": "already_processed"}

    # Process the purchase
    async with AsyncSessionLocal() as db_session:
        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            logger.error("User not found for Stripe payment: %s", telegram_id)
            return {"status": "error", "reason": "user_not_found"}

    result = {"user_id": user.id, "item_type": item_type, "item_name": item_name}

    if item_type == "subscription":
        purchase = await process_subscription_purchase(user.id, item_name)
        result.update(purchase)
        credits_added = purchase["credits_added"]
    elif item_type == "pack":
        purchase = await process_credit_pack_purchase(user.id, item_name)
        result.update(purchase)
        credits_added = purchase["credits_added"]
    else:
        return {"status": "error", "reason": "unknown_item_type"}

    # Record payment in database
    async with AsyncSessionLocal() as db_session:
        payment_repo = PaymentRepository(db_session)
        await payment_repo.create(
            user_id=user.id,
            amount=session["amount_total"] / 100,
            currency=session["currency"].upper(),
            provider="stripe",
            payment_type=item_type,
            plan_name=item_name,
            credits_added=credits_added,
            status="completed",
            provider_payment_id=payment_id,
        )

    logger.info(
        "Stripe payment processed: %s %s for user %d, credits: %d",
        item_type, item_name, user.id, credits_added,
    )

    result["status"] = "success"
    return result


# Need to import select for the duplicate check
from sqlalchemy import select


class PaymentRepository:
    """Repository for payment records."""

    def __init__(self, session):
        self.session = session

    async def create(self, **kwargs) -> Payment:
        payment = Payment(**kwargs)
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
