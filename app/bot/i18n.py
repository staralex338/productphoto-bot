"""
Internationalization (i18n) module for the bot.

Supports English and Russian languages.
All UI text, messages, and keyboard labels are centralized here.
"""

from app.config import get_settings

settings = get_settings()

# Default language
DEFAULT_LANG = "en"

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
}


class Translator:
    """Simple translator that returns text based on language code."""

    def __init__(self, lang: str = DEFAULT_LANG):
        self.lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANG

    def set_language(self, lang: str) -> None:
        """Change translator language."""
        self.lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANG

    def t(self, key: str, **kwargs) -> str:
        """Get translated text by key."""
        text = _TRANSLATIONS.get(key, {}).get(self.lang, key)
        return text.format(**kwargs) if kwargs else text


# =============================================================================
# Translations dictionary
# =============================================================================

_TRANSLATIONS = {
    # --- Language Selection ---
    "choose_language": {
        "en": "🌍 <b>Choose your language</b>",
        "ru": "🌍 <b>Выберите язык</b>",
    },

    # --- Welcome & Main Menu ---
    "welcome": {
        "en": """👋 <b>Welcome to {app_name}!</b>

Transform your product photos into stunning AI-generated commercial images in 3 simple steps:

1️⃣ <b>Upload</b> a photo of your product
2️⃣ <b>Choose</b> a style
3️⃣ <b>Receive</b> professional images

✨ <b>Free start:</b> {free_credits} credits
🎨 <b>Styles:</b> White Background, Lifestyle, Studio Premium, Social Media Ad

Use the menu below or simply send me a product photo to get started!""",
        "ru": """👋 <b>Добро пожаловать в {app_name}!</b>

Превратите фотографии ваших товаров в потрясающие AI-сгенерированные коммерческие изображения в 3 простых шага:

1️⃣ <b>Загрузите</b> фото товара
2️⃣ <b>Выберите</b> стиль
3️⃣ <b>Получите</b> профессиональные изображения

✨ <b>Стартовый бонус:</b> {free_credits} кредитов
🎨 <b>Стили:</b> Белый фон, Лайфстайл, Премиум студия, Реклама для соцсетей

Используйте меню ниже или просто отправьте фото товара, чтобы начать!""",
    },

    "help": {
        "en": """<b>How to use {app_name}</b>

📸 <b>Generate Photos</b>
Send any product photo (JPG, PNG, WEBP, max {max_size}MB, min {min_dim}×{min_dim}px).
The bot will remove the background and generate professional images.

🎨 <b>Styles</b>
• <b>White Background</b> — Clean catalog photo
• <b>Lifestyle</b> — Product in a beautiful scene
• <b>Studio Premium</b> — Luxury advertising look
• <b>Social Media Ad</b> — Viral ad aesthetic

💰 <b>Credits</b>
• 1 generation = 1 credit
• 1 upscale = 1 credit
• Get free credits by inviting friends

📜 <b>Commands</b>
/start — Main menu
/balance — Check credits
/history — Past generations
/help — This message

Need support? Contact @support_username""",
        "ru": """<b>Как использовать {app_name}</b>

📸 <b>Генерация фото</b>
Отправьте любое фото товара (JPG, PNG, WEBP, макс {max_size}МБ, мин {min_dim}×{min_dim}px).
Бот удалит фон и сгенерирует профессиональные изображения.

🎨 <b>Стили</b>
• <b>Белый фон</b> — Чистое фото для каталога
• <b>Лайфстайл</b> — Товар в красивой обстановке
• <b>Премиум студия</b> — Роскошная рекламная съёмка
• <b>Реклама для соцсетей</b> — Вирусная эстетика

💰 <b>Кредиты</b>
• 1 генерация = 1 кредит
• 1 апскейл = 1 кредит
• Получайте бесплатные кредиты, приглашая друзей

📜 <b>Команды</b>
/start — Главное меню
/balance — Проверить кредиты
/history — История генераций
/help — Это сообщение

Нужна помощь? Напишите @support_username""",
    },

    # --- Buttons ---
    "btn_generate": {"en": "📸 Generate Photo", "ru": "📸 Сгенерировать фото"},
    "btn_buy": {"en": "💰 Buy Credits", "ru": "💰 Купить кредиты"},
    "btn_history": {"en": "📜 History", "ru": "📜 История"},
    "btn_profile": {"en": "👤 Profile", "ru": "👤 Профиль"},
    "btn_referral": {"en": "🎁 Referral Program", "ru": "🎁 Реферальная программа"},
    "btn_help": {"en": "❓ Help", "ru": "❓ Помощь"},
    "btn_back": {"en": "🔙 Back", "ru": "🔙 Назад"},
    "btn_main_menu": {"en": "🏠 Main Menu", "ru": "🏠 Главное меню"},
    "btn_language": {"en": "🌍 Language", "ru": "🌍 Язык"},
    "btn_confirm": {"en": "✅ Confirm", "ru": "✅ Подтвердить"},
    "btn_cancel": {"en": "❌ Cancel", "ru": "❌ Отмена"},

    # --- Styles ---
    "style_white_background": {"en": "⚪ White Background", "ru": "⚪ Белый фон"},
    "style_lifestyle": {"en": "🏠 Lifestyle", "ru": "🏠 Лайфстайл"},
    "style_studio_premium": {"en": "💎 Studio Premium", "ru": "💎 Премиум студия"},
    "style_social_media": {"en": "📱 Social Media Ad", "ru": "📱 Реклама для соцсетей"},

    # --- Generation Flow ---
    "ask_upload": {
        "en": (
            "📤 <b>Send me a product photo</b>\n\n"
            "Requirements:\n"
            "• Format: JPG, PNG, WEBP\n"
            "• Max size: {max_size} MB\n"
            "• Min dimensions: {min_dim}×{min_dim}px\n\n"
            "The product should be clearly visible and well-lit."
        ),
        "ru": (
            "📤 <b>Отправьте фото товара</b>\n\n"
            "Требования:\n"
            "• Формат: JPG, PNG, WEBP\n"
            "• Макс. размер: {max_size} МБ\n"
            "• Мин. размер: {min_dim}×{min_dim}px\n\n"
            "Товар должен быть хорошо виден и освещён."
        ),
    },

    "photo_received": {
        "en": "✅ Photo received!\n\nNow choose a generation style:",
        "ru": "✅ Фото получено!\n\nТеперь выберите стиль генерации:",
    },

    "invalid_photo": {
        "en": (
            "❌ <b>Invalid image</b>\n\n"
            "Please send a valid image file (JPG, PNG, WEBP) "
            "with minimum dimensions {min_dim}×{min_dim}px and max size {max_size} MB."
        ),
        "ru": (
            "❌ <b>Неверное изображение</b>\n\n"
            "Отправьте корректный файл (JPG, PNG, WEBP) "
            "минимум {min_dim}×{min_dim}px и максимум {max_size} МБ."
        ),
    },

    "generation_started": {
        "en": (
            "⏳ <b>Generating your images...</b>\n\n"
            "Style: <b>{style}</b>\n"
            "This usually takes 10–30 seconds.\n\n"
            "You will receive the results automatically."
        ),
        "ru": (
            "⏳ <b>Генерация изображений...</b>\n\n"
            "Стиль: <b>{style}</b>\n"
            "Обычно занимает 10–30 секунд.\n\n"
            "Результаты придут автоматически."
        ),
    },

    "generation_error": {
        "en": (
            "❌ <b>Generation failed</b>\n\n"
            "Something went wrong while generating your images. "
            "Your credits have <b>not</b> been deducted.\n\n"
            "Please try again or contact support if the issue persists."
        ),
        "ru": (
            "❌ <b>Ошибка генерации</b>\n\n"
            "Что-то пошло не так при генерации изображений. "
            "Ваши кредиты <b>не списаны</b>.\n\n"
            "Попробуйте ещё раз или обратитесь в поддержку."
        ),
    },

    # --- Balance & Profile ---
    "balance": {
        "en": (
            "👤 <b>Your Profile</b>\n\n"
            "💳 <b>Credits:</b> {credits}\n"
            "📅 <b>Plan:</b> {plan}\n"
            "🎁 <b>Referral code:</b> <code>{referral_code}</code>\n\n"
            "Invite friends and earn <b>{referral_bonus}</b> credits for each signup!"
        ),
        "ru": (
            "👤 <b>Ваш профиль</b>\n\n"
            "💳 <b>Кредиты:</b> {credits}\n"
            "📅 <b>Тариф:</b> {plan}\n"
            "🎁 <b>Реферальный код:</b> <code>{referral_code}</code>\n\n"
            "Приглашайте друзей и получайте <b>{referral_bonus}</b> кредитов за каждого!"
        ),
    },

    # --- History ---
    "history_empty": {
        "en": (
            "📜 <b>Your History</b>\n\n"
            "You haven't generated any images yet.\n"
            "Send a product photo to get started!"
        ),
        "ru": (
            "📜 <b>Ваша история</b>\n\n"
            "Вы ещё не генерировали изображения.\n"
            "Отправьте фото товара, чтобы начать!"
        ),
    },

    "history_title": {
        "en": "📜 <b>Your Last Generations</b>\n",
        "ru": "📜 <b>Ваши последние генерации</b>\n",
    },

    # --- Referral ---
    "referral": {
        "en": (
            "🎁 <b>Referral Program</b>\n\n"
            "Share your link and earn credits!\n\n"
            "• You get: <b>+{inviter_bonus}</b> credits per friend\n"
            "• Friend gets: <b>+{invited_bonus}</b> free credits\n\n"
            "Your referral link:\n"
            "<code>{referral_link}</code>\n\n"
            "Total friends invited: <b>{total_invited}</b>\n"
            "Credits earned from referrals: <b>{credits_earned}</b>"
        ),
        "ru": (
            "🎁 <b>Реферальная программа</b>\n\n"
            "Делитесь ссылкой и зарабатывайте кредиты!\n\n"
            "• Вы получаете: <b>+{inviter_bonus}</b> кредитов за друга\n"
            "• Друг получает: <b>+{invited_bonus}</b> бесплатных кредитов\n\n"
            "Ваша реферальная ссылка:\n"
            "<code>{referral_link}</code>\n\n"
            "Всего приглашено друзей: <b>{total_invited}</b>\n"
            "Кредитов заработано: <b>{credits_earned}</b>"
        ),
    },

    "btn_share": {"en": "📤 Share with Friends", "ru": "📤 Поделиться с друзьями"},

    # --- Payments ---
    "payment_choose": {
        "en": (
            "💰 <b>Buy Credits</b>\n\n"
            "Choose a subscription plan or a one-time credit pack:"
        ),
        "ru": (
            "💰 <b>Покупка кредитов</b>\n\n"
            "Выберите подписку или разовый пакет:"
        ),
    },

    "not_enough_credits": {
        "en": (
            "❌ <b>Not enough credits</b>\n\n"
            "You need <b>{required}</b> credits but only have <b>{available}</b>.\n\n"
            "Top up your balance below:"
        ),
        "ru": (
            "❌ <b>Недостаточно кредитов</b>\n\n"
            "Нужно <b>{required}</b> кредитов, но у вас только <b>{available}</b>.\n\n"
            "Пополните баланс ниже:"
        ),
    },

    "payment_method": {
        "en": (
            "💳 <b>Choose Payment Method</b>\n\n"
            "Item: <b>{item_name}</b>\n"
            "Price: <b>{price}</b>\n\n"
            "Select how you want to pay:"
        ),
        "ru": (
            "💳 <b>Выберите способ оплаты</b>\n\n"
            "Товар: <b>{item_name}</b>\n"
            "Цена: <b>{price}</b>\n\n"
            "Выберите, как хотите оплатить:"
        ),
    },

    "payment_success_stars": {
        "en": (
            "✅ <b>Payment Successful!</b>\n\n"
            "Item: <b>{item_name}</b>\n"
            "Credits added: <b>+{credits_added}</b>\n"
            "Your new balance: <b>{new_balance}</b>\n\n"
            "Thank you for your purchase! 🎉"
        ),
        "ru": (
            "✅ <b>Оплата прошла успешно!</b>\n\n"
            "Товар: <b>{item_name}</b>\n"
            "Кредитов добавлено: <b>+{credits_added}</b>\n"
            "Новый баланс: <b>{new_balance}</b>\n\n"
            "Спасибо за покупку! 🎉"
        ),
    },

    "payment_success_stripe": {
        "en": (
            "✅ <b>Payment Successful!</b>\n\n"
            "Your payment has been processed.\n"
            "Credits will be added to your account shortly.\n\n"
            "Thank you for your purchase! 🎉"
        ),
        "ru": (
            "✅ <b>Оплата прошла успешно!</b>\n\n"
            "Ваш платёж обработан.\n"
            "Кредиты скоро появятся на счету.\n\n"
            "Спасибо за покупку! 🎉"
        ),
    },

    "payment_failed": {
        "en": (
            "❌ <b>Payment Failed</b>\n\n"
            "Something went wrong with your payment. "
            "No credits have been deducted.\n\n"
            "Please try again or contact support."
        ),
        "ru": (
            "❌ <b>Ошибка оплаты</b>\n\n"
            "Что-то пошло не так с вашим платежом. "
            "Кредиты не списаны.\n\n"
            "Попробуйте ещё раз или обратитесь в поддержку."
        ),
    },

    "btn_pay_stars": {"en": "⭐ Pay with Telegram Stars", "ru": "⭐ Оплатить Stars"},
    "btn_pay_card": {"en": "💳 Pay with Card (Stripe)", "ru": "💳 Оплатить картой (Stripe)"},

    "btn_starter": {"en": "🚀 Starter — 100 cr/mo", "ru": "🚀 Стартер — 100 кр/мес"},
    "btn_pro": {"en": "⭐ Pro — 500 cr/mo", "ru": "⭐ Про — 500 кр/мес"},

    "btn_regenerate": {"en": "🔄 Regenerate", "ru": "🔄 Перегенерировать"},
    "btn_upscale": {"en": "🔍 Upscale", "ru": "🔍 Увеличить"},

    # --- Admin ---
    "admin_dashboard": {
        "en": (
            "📊 <b>Admin Dashboard</b>\n\n"
            "👥 <b>Users:</b> {total_users} total\n"
            "   • Today: +{new_today}\n"
            "   • Week: +{new_week}\n"
            "   • Month: +{new_month}\n\n"
            "🎨 <b>Generations:</b> {total_generations} total | {gen_today} today\n\n"
            "💰 <b>Revenue:</b> ${total_revenue} total | ${revenue_today} today"
        ),
        "ru": (
            "📊 <b>Панель администратора</b>\n\n"
            "👥 <b>Пользователи:</b> {total_users} всего\n"
            "   • Сегодня: +{new_today}\n"
            "   • Неделя: +{new_week}\n"
            "   • Месяц: +{new_month}\n\n"
            "🎨 <b>Генерации:</b> {total_generations} всего | {gen_today} сегодня\n\n"
            "💰 <b>Доход:</b> ${total_revenue} всего | ${revenue_today} сегодня"
        ),
    },

    "admin_refresh": {"en": "🔄 Refresh", "ru": "🔄 Обновить"},
    "admin_users": {"en": "👤 Users", "ru": "👤 Пользователи"},
    "admin_generations": {"en": "🎨 Generations", "ru": "🎨 Генерации"},
    "admin_broadcast": {"en": "📢 Broadcast", "ru": "📢 Рассылка"},
    "admin_back": {"en": "🔙 Back", "ru": "🔙 Назад"},

    "admin_users_title": {
        "en": "👤 <b>Users Management</b>\n\nComing soon...",
        "ru": "👤 <b>Управление пользователями</b>\n\nВ разработке...",
    },

    "admin_generations_title": {
        "en": "🎨 <b>Generations Management</b>\n\nComing soon...",
        "ru": "🎨 <b>Управление генерациями</b>\n\nВ разработке...",
    },

    "admin_broadcast_title": {
        "en": "📢 <b>Broadcast</b>\n\nComing soon...",
        "ru": "📢 <b>Рассылка</b>\n\nВ разработке...",
    },

    "admin_users_list": {
        "en": "👤 <b>Users</b> (page {page}/{total})\n\nSelect a user:",
        "ru": "👤 <b>Пользователи</b> (страница {page}/{total})\n\nВыберите пользователя:",
    },

    "admin_user_not_found": {
        "en": "❌ User not found.",
        "ru": "❌ Пользователь не найден.",
    },

    "admin_user_detail": {
        "en": (
            "👤 <b>User Profile</b>\n\n"
            "🆔 ID: <code>{telegram_id}</code>\n"
            "👤 Username: @{username}\n"
            "💳 Credits: <b>{credits}</b>\n"
            "🌍 Language: {language}\n"
            "📅 Plan: {plan}\n"
            "🎁 Referral code: <code>{referral_code}</code>\n"
            "📆 Registered: {created_at}\n"
            "🚫 Status: {status}"
        ),
        "ru": (
            "👤 <b>Профиль пользователя</b>\n\n"
            "🆔 ID: <code>{telegram_id}</code>\n"
            "👤 Username: @{username}\n"
            "💳 Кредиты: <b>{credits}</b>\n"
            "🌍 Язык: {language}\n"
            "📅 Тариф: {plan}\n"
            "🎁 Реферальный код: <code>{referral_code}</code>\n"
            "📆 Зарегистрирован: {created_at}\n"
            "🚫 Статус: {status}"
        ),
    },

    "admin_credits_added": {
        "en": "✅ Added <b>+{amount}</b> credits to user. New balance: <b>{balance}</b>",
        "ru": "✅ Добавлено <b>+{amount}</b> кредитов. Новый баланс: <b>{balance}</b>",
    },

    "admin_credits_removed": {
        "en": "✅ Removed <b>-{amount}</b> credits. New balance: <b>{balance}</b>",
        "ru": "✅ Снято <b>-{amount}</b> кредитов. Новый баланс: <b>{balance}</b>",
    },

    "admin_user_banned": {
        "en": "🚫 User <b>banned</b>.",
        "ru": "🚫 Пользователь <b>забанен</b>.",
    },

    "admin_user_unbanned": {
        "en": "✅ User <b>unbanned</b>.",
        "ru": "✅ Пользователь <b>разбанен</b>.",
    },

    "admin_user_history": {
        "en": "🎨 <b>Generation History</b> for user:\n\n{items}",
        "ru": "🎨 <b>История генераций</b> пользователя:\n\n{items}",
    },

    "admin_history_empty": {
        "en": "No generations yet.",
        "ru": "Пока нет генераций.",
    },

    "admin_search_prompt": {
        "en": "🔍 <b>Search user</b>\n\nEnter username or Telegram ID:",
        "ru": "🔍 <b>Поиск пользователя</b>\n\nВведите @username или Telegram ID:",
    },

    "admin_search_no_results": {
        "en": "❌ No users found.",
        "ru": "❌ Пользователи не найдены.",
    },

    # --- Errors / Misc ---
    "please_start": {
        "en": "Please send /start first.",
        "ru": "Пожалуйста, сначала отправьте /start.",
    },

    "user_not_found": {
        "en": "User not found. Send /start",
        "ru": "Пользователь не найден. Отправьте /start",
    },

    "referral_bonus": {
        "en": (
            "🎉 <b>Welcome bonus!</b>\n\n"
            "You were invited by a friend and received "
            "<b>+{bonus_invited}</b> bonus credits!\n\n"
            "Your friend also got <b>+{bonus_inviter}</b> credits. 🎁"
        ),
        "ru": (
            "🎉 <b>Бонус за регистрацию!</b>\n\n"
            "Вас пригласил друг, и вы получили "
            "<b>+{bonus_invited}</b> бонусных кредитов!\n\n"
            "Ваш друг тоже получил <b>+{bonus_inviter}</b> кредитов. 🎁"
        ),
    },

    # --- Generation Actions ---
    "generation_complete": {
        "en": "✅ Generation complete! What would you like to do next?",
        "ru": "✅ Генерация завершена! Что хотите сделать дальше?",
    },

    "regenerating": {
        "en": "Regenerating...",
        "ru": "Перегенерация...",
    },

    "upscaling": {
        "en": "Upscaling...",
        "ru": "Увеличение разрешения...",
    },

    "upscale_started": {
        "en": "🔍 <b>Upscale started!</b>\n\nThis will take a few seconds...",
        "ru": "🔍 <b>Апскейл запущен!</b>\n\nЭто займёт несколько секунд...",
    },

    "upscale_complete": {
        "en": "🔍 <b>Upscaled 2x</b>\n\n✅ Your image has been enhanced!",
        "ru": "🔍 <b>Увеличено в 2 раза</b>\n\n✅ Изображение улучшено!",
    },

    "upscale_error_not_found": {
        "en": "❌ Cannot upscale: generation not found or not completed.",
        "ru": "❌ Невозможно увеличить: генерация не найдена или не завершена.",
    },

    "upscale_error_no_images": {
        "en": "❌ No images found to upscale.",
        "ru": "❌ Не найдено изображений для апскейла.",
    },

    # --- Errors ---
    "send_photo": {
        "en": "Send me a product photo!",
        "ru": "Отправьте фото товара!",
    },

    "session_expired": {
        "en": "Your session has expired. Please start again with /start.",
        "ru": "Сессия истекла. Пожалуйста, начните заново с /start.",
    },

    "generation_not_found": {
        "en": "Generation not found.",
        "ru": "Генерация не найдена.",
    },

    "could_not_deduct": {
        "en": "Could not deduct credits. Try again.",
        "ru": "Не удалось списать кредиты. Попробуйте ещё раз.",
    },

    "unknown_item_type": {
        "en": "Unknown item type.",
        "ru": "Неизвестный тип товара.",
    },

    "payment_setup_failed": {
        "en": "Payment setup failed. Try again.",
        "ru": "Ошибка настройки оплаты. Попробуйте ещё раз.",
    },

    # --- Image Validation ---
    "image_too_large": {
        "en": "Image too large ({size:.1f} MB). Max: {max_mb} MB.",
        "ru": "Изображение слишком большое ({size:.1f} МБ). Максимум: {max_mb} МБ.",
    },

    "unsupported_format": {
        "en": "Unsupported format: {format}. Use JPG, PNG, or WEBP.",
        "ru": "Неподдерживаемый формат: {format}. Используйте JPG, PNG или WEBP.",
    },

    "image_too_small": {
        "en": "Image too small ({width}×{height}). Minimum: {min_dim}×{min_dim}px.",
        "ru": "Изображение слишком маленькое ({width}×{height}). Минимум: {min_dim}×{min_dim}px.",
    },

    "could_not_read_image": {
        "en": "Could not read image file. Please try another image.",
        "ru": "Не удалось прочитать файл изображения. Попробуйте другое изображение.",
    },
}
