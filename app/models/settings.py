"""
Dynamic settings model — allows changing bot config via admin panel.

Key-value store for runtime configuration.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.engine import Base


class BotSetting(Base):
    """Dynamic key-value setting."""

    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="Setting key",
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Setting value (JSON string for complex values)",
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Human-readable description",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BotSetting(key={self.key}, value={self.value})>"
