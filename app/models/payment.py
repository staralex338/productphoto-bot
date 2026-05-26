"""
Payment model — tracks all payment transactions.

Supports Telegram Stars and Stripe payments.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


class Payment(Base):
    """Record of a payment transaction."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Amount paid (in smallest currency unit: cents for USD, stars for Telegram)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Amount paid",
    )

    # Currency or unit
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
        comment="USD, RUB, or XTR (Telegram Stars)",
    )

    # Provider
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="telegram_stars | stripe",
    )

    # What was purchased
    payment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="subscription | credit_pack",
    )

    # Plan or pack details
    plan_name: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="starter | pro | pack_50 | pack_100 | pack_500",
    )

    # Credits added to user account
    credits_added: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of credits added by this payment",
    )

    # Payment status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending | completed | failed | refunded",
    )

    # External transaction ID
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="Stripe payment intent ID or Telegram charge ID",
    )

    # Error or notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional payment info or error messages",
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

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
