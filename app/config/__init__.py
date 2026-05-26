"""
Application configuration module.

Uses Pydantic Settings to load and validate environment variables.
All configuration is centralized here for easy maintenance.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ============================================
    # Bot Configuration
    # ============================================
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_webhook_url: str = Field(..., description="Public URL for Telegram webhook")
    telegram_webhook_secret: str = Field(default="", description="Secret token for webhook validation")

    # ============================================
    # Database Configuration (Supabase)
    # ============================================
    database_url: str = Field(..., description="PostgreSQL connection string (asyncpg)")
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service role key")
    supabase_storage_bucket: str = Field(default="product-images", description="Supabase Storage bucket name")

    # ============================================
    # AI Providers
    # ============================================
    fal_key: str = Field(..., description="Fal.ai API key")
    replicate_api_token: Optional[str] = Field(default=None, description="Replicate API token (fallback)")
    remove_bg_api_key: Optional[str] = Field(default=None, description="Remove.bg API key")
    clipdrop_api_key: Optional[str] = Field(default=None, description="ClipDrop API key (fallback bg removal)")

    # ============================================
    # Payment Providers
    # ============================================
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook endpoint secret")
    telegram_payment_provider_token: Optional[str] = Field(default=None, description="Telegram Payments provider token")

    # ============================================
    # Application Settings
    # ============================================
    app_name: str = Field(default="ProductPhoto AI", description="Application display name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # ============================================
    # Business Logic Settings
    # ============================================
    free_credits_on_start: int = Field(default=3, description="Free credits for new users")
    referral_bonus_inviter: int = Field(default=10, description="Credits given to referrer")
    referral_bonus_invited: int = Field(default=5, description="Credits given to invited user")

    # Generation settings
    max_image_size_mb: int = Field(default=10, description="Max uploaded image size in MB")
    min_image_dimension: int = Field(default=512, description="Minimum image width/height in pixels")
    default_generations_count: int = Field(default=4, description="Number of images generated per request")
    storage_ttl_days: int = Field(default=30, description="Storage TTL for images")
    daily_generation_limit: int = Field(default=50, description="Max generations per user per day")

    # Queue settings
    max_concurrent_generations: int = Field(default=5, description="Max parallel generation tasks")
    generation_timeout_seconds: int = Field(default=120, description="Timeout for AI generation requests")

    # ============================================
    # Validators
    # ============================================
    @validator("database_url", pre=True)
    def fix_database_url(cls, v: str) -> str:
        """Convert Supabase connection string to asyncpg format if needed."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def max_image_size_bytes(self) -> int:
        """Return max image size in bytes."""
        return self.max_image_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached Settings instance.

    Using lru_cache ensures settings are loaded only once per process,
    improving performance and maintaining consistency.
    """
    return Settings()
