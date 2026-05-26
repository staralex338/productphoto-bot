"""
Database repositories — encapsulate all CRUD logic.

Contains UserRepository and GenerationRepository.
"""

from datetime import datetime, timezone

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.generation import Generation
from app.models.payment import Payment
from app.models.user import User

settings = get_settings()


# =============================================================================
# User Repository
# =============================================================================


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch a user by their Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> User | None:
        """Fetch a user by their referral code."""
        result = await self.session.execute(
            select(User).where(User.referral_code == code)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        invited_by: int | None = None,
        language: str = "en",
    ) -> User:
        """Create a new user with free starting credits."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            credits=settings.free_credits_on_start,
            invited_by=invited_by,
            language=language,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
    ) -> tuple[User, bool]:
        """Get existing user or create a new one. Returns (user, is_new)."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            if username and user.username != username:
                user.username = username
                await self.session.commit()
            return user, False
        return await self.create_user(telegram_id, username), True

    async def add_credits(self, user_id: int, amount: int) -> int:
        """Add credits to a user's balance. Returns new balance."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=User.credits + amount)
            .returning(User.credits)
        )
        await self.session.commit()
        return result.scalar_one()

    async def deduct_credits(self, user_id: int, amount: int) -> bool:
        """Deduct credits if user has enough. Returns True if successful."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id, User.credits >= amount)
            .values(credits=User.credits - amount)
            .returning(User.credits)
        )
        await self.session.commit()
        return result.scalar_one_or_none() is not None

    async def set_subscription(self, user_id: int, plan: str) -> None:
        """Update user's subscription plan."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(subscription_type=plan)
        )
        await self.session.commit()

    async def set_language(self, user_id: int, language: str) -> None:
        """Update user's language preference."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(language=language)
        )
        await self.session.commit()

    async def get_total_users(self) -> int:
        """Get total number of registered users."""
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def get_new_users_count(self, since: datetime) -> int:
        """Count users registered since given datetime."""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.created_at >= since)
        )
        return result.scalar_one()


# =============================================================================
# Generation Repository
# =============================================================================


class GenerationRepository:
    """Repository for generation-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        original_image_url: str,
        generation_type: str,
        model_used: str = "flux_schnell",
        credits_spent: int = 1,
    ) -> Generation:
        """Create a new generation record with 'pending' status."""
        generation = Generation(
            user_id=user_id,
            original_image_url=original_image_url,
            generated_image_url="",
            generation_type=generation_type,
            model_used=model_used,
            status="pending",
            credits_spent=credits_spent,
        )
        self.session.add(generation)
        await self.session.commit()
        await self.session.refresh(generation)
        return generation

    async def get_by_id(self, generation_id: int) -> Generation | None:
        """Fetch a generation by ID."""
        result = await self.session.execute(
            select(Generation).where(Generation.id == generation_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        generation_id: int,
        status: str,
        generated_image_url: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update generation status and optional fields."""
        generation = await self.get_by_id(generation_id)
        if not generation:
            return

        generation.status = status
        if generated_image_url is not None:
            generation.generated_image_url = generated_image_url
        if error_message is not None:
            generation.error_message = error_message
        if status in ("completed", "failed"):
            generation.completed_at = datetime.now(timezone.utc)

        await self.session.commit()

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Generation]:
        """Fetch user's generation history, newest first."""
        result = await self.session.execute(
            select(Generation)
            .where(Generation.user_id == user_id)
            .order_by(desc(Generation.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count_user_generations_today(self, user_id: int) -> int:
        """Count how many generations user started today."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(func.count(Generation.id)).where(
                Generation.user_id == user_id,
                Generation.created_at >= today_start,
            )
        )
        return result.scalar_one()

    async def get_total_generations(self) -> int:
        """Get total number of all generations."""
        result = await self.session.execute(select(func.count(Generation.id)))
        return result.scalar_one()

    async def get_generations_count(self, since: datetime) -> int:
        """Count generations created since given datetime."""
        result = await self.session.execute(
            select(func.count(Generation.id)).where(Generation.created_at >= since)
        )
        return result.scalar_one()


# =============================================================================
# Payment Repository
# =============================================================================


class PaymentRepository:
    """Repository for payment transaction records."""

    def __init__(self, session):
        self.session = session

    async def create(self, **kwargs) -> Payment:
        """Create a new payment record."""
        payment = Payment(**kwargs)
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_by_provider_id(self, provider_payment_id: str) -> Payment | None:
        """Fetch payment by provider transaction ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        return result.scalar_one_or_none()

    async def get_user_payments(self, user_id: int, limit: int = 20) -> list[Payment]:
        """Fetch user's payment history, newest first."""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(desc(Payment.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_total_revenue(self) -> float:
        """Get total revenue from all completed payments."""
        result = await self.session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "completed")
        )
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0

    async def get_revenue(self, since: datetime) -> float:
        """Get revenue from completed payments since given datetime."""
        result = await self.session.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == "completed",
                Payment.created_at >= since,
            )
        )
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0
