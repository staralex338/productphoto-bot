"""
Inline keyboards and reply markup builders for the bot.

Uses aiogram 3.x InlineKeyboardBuilder for clean, type-safe buttons.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =============================================================================
# Main Menu
# =============================================================================


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu shown after /start or when user taps 'Menu'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📸 Generate Photo", callback_data="menu:generate"),
        InlineKeyboardButton(text="💰 Buy Credits", callback_data="menu:buy"),
    )
    builder.row(
        InlineKeyboardButton(text="📜 History", callback_data="menu:history"),
        InlineKeyboardButton(text="👤 Profile", callback_data="menu:profile"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Referral Program", callback_data="menu:referral"),
        InlineKeyboardButton(text="❓ Help", callback_data="menu:help"),
    )
    return builder.as_markup()


# =============================================================================
# Style Selection
# =============================================================================


def style_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for choosing generation style.

    Each button maps to a generation style that determines the AI prompt.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⚪ White Background",
            callback_data="style:white_background",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 Lifestyle",
            callback_data="style:lifestyle",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💎 Studio Premium",
            callback_data="style:studio_premium",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📱 Social Media Ad",
            callback_data="style:social_media_ad",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Generation Result Actions
# =============================================================================


def generation_result_keyboard(generation_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard shown under generated images.

    Args:
        generation_id: Database ID of the generation record.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 Regenerate",
            callback_data=f"action:regenerate:{generation_id}",
        ),
        InlineKeyboardButton(
            text="🔍 Upscale",
            callback_data=f"action:upscale:{generation_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Credit Packs & Subscriptions
# =============================================================================


def buy_credits_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for purchasing credit packs and subscriptions."""
    builder = InlineKeyboardBuilder()
    # Subscription plans
    builder.row(
        InlineKeyboardButton(
            text="🚀 Starter — 100 cr/mo",
            callback_data="buy:subscription:starter",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⭐ Pro — 500 cr/mo",
            callback_data="buy:subscription:pro",
        )
    )
    # One-time packs
    builder.row(
        InlineKeyboardButton(text="50 credits", callback_data="buy:pack:50"),
        InlineKeyboardButton(text="100 credits", callback_data="buy:pack:100"),
        InlineKeyboardButton(text="500 credits", callback_data="buy:pack:500"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="menu:main"),
    )
    return builder.as_markup()


def payment_method_keyboard(item_type: str, item_name: str) -> InlineKeyboardMarkup:
    """
    Keyboard for choosing payment method.

    Args:
        item_type: "subscription" or "pack"
        item_name: Plan or pack identifier
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⭐ Pay with Telegram Stars",
            callback_data=f"pay:stars:{item_type}:{item_name}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💳 Pay with Card (Stripe)",
            callback_data=f"pay:stripe:{item_type}:{item_name}",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="menu:buy"),
    )
    return builder.as_markup()


# =============================================================================
# Referral
# =============================================================================


def referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """Keyboard for sharing referral link."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📤 Share with Friends",
            url=f"https://t.me/share/url?url={referral_link}&text=Get%20free%20AI%20product%20photos!",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Confirm / Cancel
# =============================================================================


def confirm_cancel_keyboard(confirm_callback: str, cancel_callback: str = "menu:main") -> InlineKeyboardMarkup:
    """Generic confirm/cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Confirm", callback_data=confirm_callback),
        InlineKeyboardButton(text="❌ Cancel", callback_data=cancel_callback),
    )
    return builder.as_markup()
