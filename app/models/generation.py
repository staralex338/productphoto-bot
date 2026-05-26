"""
Generation model — stores metadata about each AI image generation.

Images themselves are stored in Supabase Storage; we only store URLs here.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


class Generation(Base):
    """Record of a single image generation request."""

    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Original uploaded image URL (in Supabase Storage)
    original_image_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="URL of original product photo",
    )

    # Generated image URL(s) — comma-separated if multiple
    generated_image_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Comma-separated URLs of generated images",
    )

    # Style used for generation
    generation_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="white_background | lifestyle | studio_premium | social_media_ad",
    )

    # AI model used
    model_used: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="flux_schnell",
        comment="flux_schnell | flux_dev | etc.",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending | processing | completed | failed",
    )

    # Error message if failed
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if generation failed",
    )

    # How many credits were spent
    credits_spent: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Credits deducted for this generation",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When generation finished",
    )

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="generations")

    def __repr__(self) -> str:
        return f"<Generation(id={self.id}, user_id={self.user_id}, type={self.generation_type}, status={self.status})>"
