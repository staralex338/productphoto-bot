"""
Referral system service.

Handles processing referral codes, crediting users, and tracking referrals.
"""

import logging

from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import UserRepository
from app.models.referral import Referral
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class ReferralError(Exception):
    """Base exception for referral errors."""
    pass


class SelfReferralError(ReferralError):
    """User tried to refer themselves."""
    pass


class AlreadyReferredError(ReferralError):
    """User already used a referral code."""
    pass


class InvalidReferralCodeError(ReferralError):
    """Referral code does not exist."""
    pass


async def process_referral(
    new_user_telegram_id: int,
    referral_code: str,
) -> dict:
    """
    Process a referral when a new user signs up with a referral code.

    Args:
        new_user_telegram_id: Telegram ID of the newly created user
        referral_code: The referral code used

    Returns:
        Dict with referral result details

    Raises:
        SelfReferralError: If user tries to refer themselves
        AlreadyReferredError: If user already used a referral
        InvalidReferralCodeError: If code doesn't exist
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)

        # Get the new user
        new_user = await user_repo.get_by_telegram_id(new_user_telegram_id)
        if not new_user:
            raise ReferralError("New user not found")

        # Check if user already used a referral
        if new_user.invited_by is not None:
            raise AlreadyReferredError("User already referred by someone")

        # Find inviter by referral code
        inviter = await user_repo.get_by_referral_code(referral_code.upper())
        if not inviter:
            raise InvalidReferralCodeError(f"Invalid referral code: {referral_code}")

        # Prevent self-referral
        if inviter.telegram_id == new_user_telegram_id:
            raise SelfReferralError("Cannot refer yourself")

        # Update new user's invited_by
        new_user.invited_by = inviter.id
        await session.commit()

        # Create referral record
        referral = Referral(
            inviter_id=inviter.id,
            invited_user_id=new_user.id,
            referral_code_used=referral_code.upper(),
            reward_given=False,
        )
        session.add(referral)
        await session.commit()

        # Credit both users
        inviter_new_balance = await user_repo.add_credits(
            inviter.id, settings.referral_bonus_inviter
        )
        invited_new_balance = await user_repo.add_credits(
            new_user.id, settings.referral_bonus_invited
        )

        # Mark reward as given
        referral.reward_given = True
        await session.commit()

        logger.info(
            "Referral processed: user %d invited by %d (code: %s). "
            "Inviter credits: %d, Invited credits: %d",
            new_user.id,
            inviter.id,
            referral_code,
            settings.referral_bonus_inviter,
            settings.referral_bonus_invited,
        )

        return {
            "inviter_id": inviter.id,
            "inviter_telegram_id": inviter.telegram_id,
            "inviter_username": inviter.username,
            "inviter_new_balance": inviter_new_balance,
            "invited_new_balance": invited_new_balance,
            "referral_code": referral_code.upper(),
            "bonus_inviter": settings.referral_bonus_inviter,
            "bonus_invited": settings.referral_bonus_invited,
        }


async def get_referral_stats(user_id: int) -> dict:
    """
    Get referral statistics for a user.

    Args:
        user_id: Database user ID

    Returns:
        Dict with referral stats
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await session.get(User, user_id)  # type: ignore[var-annotated]

        if not user:
            return {"total_invited": 0, "referral_code": "", "credits_earned": 0}

        # Count successful referrals
        result = await session.execute(
            select(Referral).where(
                Referral.inviter_id == user_id,
                Referral.reward_given == True,
            )
        )
        referrals = result.scalars().all()

        total_invited = len(referrals)
        credits_earned = total_invited * settings.referral_bonus_inviter

        return {
            "total_invited": total_invited,
            "referral_code": user.referral_code,
            "credits_earned": credits_earned,
        }
