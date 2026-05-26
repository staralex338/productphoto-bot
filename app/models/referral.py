"""
Referral model — tracks who invited whom and whether rewards were given.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


class Referral(Base):
    """Record of a referral relationship between two users."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User who sent the invitation
    inviter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who was invited (signed up using the referral code)
    invited_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Referral code used
    referral_code_used: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="The referral code that was used",
    )

    # Whether rewards have been credited
    reward_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if both users received their credits",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    inviter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[inviter_id],
        back_populates="referrals_given",
    )

    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, inviter={self.inviter_id}, invited={self.invited_user_id}, rewarded={self.reward_given})>"
