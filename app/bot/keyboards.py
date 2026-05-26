"""
Inline keyboards and reply markup builders for the bot.

Uses aiogram 3.x InlineKeyboardBuilder for clean, type-safe buttons.
All labels are translated based on user's language.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.i18n import SUPPORTED_LANGUAGES, Translator


# =============================================================================
# Language Selection
# =============================================================================


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing language on first start."""
    builder = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"lang:{code}")
        )
    return builder.as_markup()


# =============================================================================
# Main Menu
# =============================================================================


def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Main menu shown after /start or when user taps 'Menu'."""
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t.t("btn_generate"), callback_data="menu:generate"),
        InlineKeyboardButton(text=t.t("btn_buy"), callback_data="menu:buy"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_history"), callback_data="menu:history"),
        InlineKeyboardButton(text=t.t("btn_profile"), callback_data="menu:profile"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_referral"), callback_data="menu:referral"),
        InlineKeyboardButton(text=t.t("btn_help"), callback_data="menu:help"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_language"), callback_data="menu:language"),
    )
    return builder.as_markup()


# =============================================================================
# Style Selection
# =============================================================================


def style_selection_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Keyboard for choosing generation style.
    """
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t.t("style_white_background"),
            callback_data="style:white_background",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t.t("style_lifestyle"),
            callback_data="style:lifestyle",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t.t("style_studio_premium"),
            callback_data="style:studio_premium",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t.t("style_social_media"),
            callback_data="style:social_media_ad",
        )
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_back"), callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Generation Result Actions
# =============================================================================


def generation_result_keyboard(generation_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Keyboard shown under generated images.
    """
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_regenerate"),
            callback_data=f"action:regenerate:{generation_id}",
        ),
        InlineKeyboardButton(
            text=t.t("btn_upscale"),
            callback_data=f"action:upscale:{generation_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_main_menu"), callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Credit Packs & Subscriptions
# =============================================================================


def buy_credits_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for purchasing credit packs and subscriptions."""
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    # Subscription plans
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_starter"),
            callback_data="buy:subscription:starter",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_pro"),
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
        InlineKeyboardButton(text=t.t("btn_back"), callback_data="menu:main"),
    )
    return builder.as_markup()


def payment_method_keyboard(item_type: str, item_name: str, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Keyboard for choosing payment method.
    """
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_pay_stars"),
            callback_data=f"pay:stars:{item_type}:{item_name}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_pay_card"),
            callback_data=f"pay:stripe:{item_type}:{item_name}",
        )
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_back"), callback_data="menu:buy"),
    )
    return builder.as_markup()


# =============================================================================
# Referral
# =============================================================================


def referral_keyboard(referral_link: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for sharing referral link."""
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t.t("btn_share"),
            url=f"https://t.me/share/url?url={referral_link}&text=Get%20free%20AI%20product%20photos!",
        )
    )
    builder.row(
        InlineKeyboardButton(text=t.t("btn_main_menu"), callback_data="menu:main"),
    )
    return builder.as_markup()


# =============================================================================
# Confirm / Cancel
# =============================================================================


def confirm_cancel_keyboard(confirm_callback: str, cancel_callback: str = "menu:main", lang: str = "en") -> InlineKeyboardMarkup:
    """Generic confirm/cancel keyboard."""
    t = Translator(lang)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t.t("btn_confirm"), callback_data=confirm_callback),
        InlineKeyboardButton(text=t.t("btn_cancel"), callback_data=cancel_callback),
    )
    return builder.as_markup()


# =============================================================================
# Admin Dashboard
# =============================================================================


def admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for admin dashboard."""
    t = Translator("ru")
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t.t("admin_refresh"), callback_data="admin:dashboard"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("admin_users"), callback_data="admin:users"),
        InlineKeyboardButton(text=t.t("admin_generations"), callback_data="admin:generations"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Финансы", callback_data="admin:fin"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin:settings"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("admin_broadcast"), callback_data="admin:broadcast"),
    )
    return builder.as_markup()


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Back to admin dashboard button."""
    t = Translator("ru")
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t.t("admin_back"), callback_data="admin:dashboard"),
    )
    return builder.as_markup()


# =============================================================================
# Admin Users
# =============================================================================


def admin_users_list_keyboard(users: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Keyboard for paginated user list."""
    t = Translator("ru")
    builder = InlineKeyboardBuilder()

    for user in users:
        status = "🚫" if user.is_banned else "✅"
        label = f"{status} {user.username or user.telegram_id} ({user.credits} cr)"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"admin:user:{user.id}")
        )

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin:users:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin:users:{page+1}"))
    if nav:
        builder.row(*nav)

    # Search
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data="admin:users:search"),
    )
    builder.row(
        InlineKeyboardButton(text=t.t("admin_back"), callback_data="admin:dashboard"),
    )
    return builder.as_markup()


def admin_user_detail_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    """Keyboard for user detail actions."""
    t = Translator("ru")
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="➕ +10 кредитов", callback_data=f"admin:user:{user_id}:add:10"),
        InlineKeyboardButton(text="➖ -10 кредитов", callback_data=f"admin:user:{user_id}:sub:10"),
    )
    builder.row(
        InlineKeyboardButton(text="➕ +100 кредитов", callback_data=f"admin:user:{user_id}:add:100"),
        InlineKeyboardButton(text="➖ -100 кредитов", callback_data=f"admin:user:{user_id}:sub:100"),
    )

    if is_banned:
        builder.row(
            InlineKeyboardButton(text="✅ Разбанить", callback_data=f"admin:user:{user_id}:unban"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🚫 Забанить", callback_data=f"admin:user:{user_id}:ban"),
        )

    builder.row(
        InlineKeyboardButton(text="🎨 История генераций", callback_data=f"admin:user:{user_id}:history"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin:users:0"),
        InlineKeyboardButton(text=t.t("admin_back"), callback_data="admin:dashboard"),
    )
    return builder.as_markup()


def admin_user_history_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Back button for user history."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 К профилю", callback_data=f"admin:user:{user_id}"),
    )
    return builder.as_markup()


# =============================================================================
# Admin Generations
# =============================================================================


def admin_generations_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu for generations management."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 По стилям", callback_data="admin:gen:styles"),
        InlineKeyboardButton(text="❌ Failed", callback_data="admin:gen:failed"),
    )
    builder.row(
        InlineKeyboardButton(text="⏳ Pending", callback_data="admin:gen:pending"),
        InlineKeyboardButton(text="✅ Completed", callback_data="admin:gen:completed"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:dashboard"),
    )
    return builder.as_markup()


def admin_generations_list_keyboard(generations: list, filter_type: str, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Keyboard for paginated generation list."""
    builder = InlineKeyboardBuilder()

    for gen in generations:
        status_icon = "✅" if gen.status == "completed" else "⏳" if gen.status == "pending" else "❌"
        label = f"{status_icon} #{gen.id} | {gen.generation_type[:15]}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"admin:gen:{gen.id}")
        )

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin:gen:{filter_type}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin:gen:{filter_type}:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:generations"),
    )
    return builder.as_markup()


def admin_generation_detail_keyboard(gen_id: int, can_retry: bool = False) -> InlineKeyboardMarkup:
    """Keyboard for generation detail."""
    builder = InlineKeyboardBuilder()
    if can_retry:
        builder.row(
            InlineKeyboardButton(text="🔄 Повторить", callback_data=f"admin:gen:{gen_id}:retry"),
        )
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin:gen:failed"),
    )
    return builder.as_markup()


# =============================================================================
# Admin Finances
# =============================================================================


def admin_finances_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu for finances."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Все платежи", callback_data="admin:fin:payments"),
    )
    builder.row(
        InlineKeyboardButton(text="⭐ Stars", callback_data="admin:fin:stars"),
        InlineKeyboardButton(text="💳 Stripe", callback_data="admin:fin:stripe"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Популярные тарифы", callback_data="admin:fin:plans"),
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Возвраты", callback_data="admin:fin:refunds"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:dashboard"),
    )
    return builder.as_markup()


# =============================================================================
# Admin Broadcast
# =============================================================================


def admin_broadcast_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu for broadcast."""
    t = Translator("ru")
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌍 Всем", callback_data="admin:bc:all"),
    )
    builder.row(
        InlineKeyboardButton(text="🇬🇧 EN", callback_data="admin:bc:lang:en"),
        InlineKeyboardButton(text="🇷🇺 RU", callback_data="admin:bc:lang:ru"),
    )
    builder.row(
        InlineKeyboardButton(text="🆓 Free", callback_data="admin:bc:plan:free"),
        InlineKeyboardButton(text="⭐ Paid", callback_data="admin:bc:plan:paid"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:dashboard"),
    )
    return builder.as_markup()


def admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm or cancel broadcast."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Отправить", callback_data="admin:bc:confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin:broadcast"),
    )
    return builder.as_markup()


# =============================================================================
# Admin Settings
# =============================================================================


def admin_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu for system settings."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Цены", callback_data="admin:set:prices"),
        InlineKeyboardButton(text="🎁 Стартовый бонус", callback_data="admin:set:bonus"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Генерация", callback_data="admin:set:gen"),
        InlineKeyboardButton(text="💧 Watermark", callback_data="admin:set:wm"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:dashboard"),
    )
    return builder.as_markup()


def admin_settings_value_keyboard(key: str) -> InlineKeyboardMarkup:
    """Back button for settings."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:settings"),
    )
    return builder.as_markup()
