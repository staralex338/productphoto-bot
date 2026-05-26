"""
User model — represents a Telegram user in the system.

Tracks credits, subscription plan, referral info, and timestamps.
"""

import secrets
import string
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


def generate_referral_code() -> str:
    """Generate a unique 8-character referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class User(Base):
    """Telegram user with credits and subscription info."""

    __tablename__ = "users"

    # Primary key — auto-increment integer
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Telegram ID — unique identifier from Telegram (can be very large, use BigInteger)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
        comment="Telegram user ID",
    )

    # Telegram username (optional, user may not have one)
    username: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="Telegram @username",
    )

    # Available credits for generation/upscale
    credits: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Available credits",
    )

    # Subscription plan
    subscription_type: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
        comment="free | starter | pro",
    )

    # Referral code for sharing
    referral_code: Mapped[str] = mapped_column(
        String(8),
        unique=True,
        default=generate_referral_code,
        nullable=False,
        comment="Unique referral code",
    )

    # Who invited this user (nullable for organic signups)
    invited_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User ID of referrer",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (lazy loading)
    generations: Mapped[list["Generation"]] = relationship(
        "Generation",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    referrals_given: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.inviter_id",
        back_populates="inviter",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def is_free(self) -> bool:
        """Check if user is on free plan."""
        return self.subscription_type == "free"

    @property
    def is_paid(self) -> bool:
        """Check if user has a paid subscription."""
        return self.subscription_type in ("starter", "pro")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, credits={self.credits}, plan={self.subscription_type})>"
