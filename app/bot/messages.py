"""
Message text templates for the bot.

Centralized here for easy copy editing and i18n (future).
All messages use HTML parse mode.
"""

from app.config import get_settings

settings = get_settings()


# =============================================================================
# Welcome & Main Menu
# =============================================================================

WELCOME_MESSAGE = """
👋 <b>Welcome to {app_name}!</b>

Transform your product photos into stunning AI-generated commercial images in 3 simple steps:

1️⃣ <b>Upload</b> a photo of your product
2️⃣ <b>Choose</b> a style
3️⃣ <b>Receive</b> professional images

✨ <b>Free start:</b> {free_credits} credits
🎨 <b>Styles:</b> White Background, Lifestyle, Studio Premium, Social Media Ad

Use the menu below or simply send me a product photo to get started!
""".format(
    app_name=settings.app_name,
    free_credits=settings.free_credits_on_start,
)

HELP_MESSAGE = """
<b>How to use {app_name}</b>

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

Need support? Contact @support_username
""".format(
    app_name=settings.app_name,
    max_size=settings.max_image_size_mb,
    min_dim=settings.min_image_dimension,
)

# =============================================================================
# Generation Flow
# =============================================================================

ASK_UPLOAD_MESSAGE = (
    "📤 <b>Send me a product photo</b>\n\n"
    "Requirements:\n"
    "• Format: JPG, PNG, WEBP\n"
    "• Max size: {max_size} MB\n"
    "• Min dimensions: {min_dim}×{min_dim}px\n\n"
    "The product should be clearly visible and well-lit."
).format(
    max_size=settings.max_image_size_mb,
    min_dim=settings.min_image_dimension,
)

PHOTO_RECEIVED_MESSAGE = (
    "✅ Photo received!\n\n"
    "Now choose a generation style:"
)

INVALID_PHOTO_MESSAGE = (
    "❌ <b>Invalid image</b>\n\n"
    "Please send a valid image file (JPG, PNG, WEBP) "
    "with minimum dimensions {min_dim}×{min_dim}px and max size {max_size} MB."
).format(
    min_dim=settings.min_image_dimension,
    max_size=settings.max_image_size_mb,
)

GENERATION_STARTED_MESSAGE = (
    "⏳ <b>Generating your images...</b>\n\n"
    "Style: <b>{style}</b>\n"
    "This usually takes 10–30 seconds.\n\n"
    "You will receive the results automatically."
)

GENERATION_ERROR_MESSAGE = (
    "❌ <b>Generation failed</b>\n\n"
    "Something went wrong while generating your images. "
    "Your credits have <b>not</b> been deducted.\n\n"
    "Please try again or contact support if the issue persists."
)

# =============================================================================
# Balance & Profile
# =============================================================================

BALANCE_MESSAGE = """
👤 <b>Your Profile</b>

💳 <b>Credits:</b> {credits}
📅 <b>Plan:</b> {plan}
🎁 <b>Referral code:</b> <code>{referral_code}</code>

Invite friends and earn <b>{referral_bonus}</b> credits for each signup!
"""

# =============================================================================
# History
# =============================================================================

HISTORY_EMPTY_MESSAGE = (
    "📜 <b>Your History</b>\n\n"
    "You haven't generated any images yet.\n"
    "Send a product photo to get started!"
)

HISTORY_ITEM_MESSAGE = (
    "📅 {date}\n"
    "🎨 {style}\n"
    "🤖 {model}\n"
    "💰 {credits} credit(s)"
)

# =============================================================================
# Referral
# =============================================================================

REFERRAL_MESSAGE = """
🎁 <b>Referral Program</b>

Share your link and earn credits!

• You get: <b>+{inviter_bonus}</b> credits per friend
• Friend gets: <b>+{invited_bonus}</b> free credits

Your referral link:
<code>{referral_link}</code>

Total friends invited: <b>{total_invited}</b>
Credits earned from referrals: <b>{credits_earned}</b>
"""

# =============================================================================
# Payments
# =============================================================================

PAYMENT_CHOOSE_MESSAGE = (
    "💰 <b>Buy Credits</b>\n\n"
    "Choose a subscription plan or a one-time credit pack:"
)

NOT_ENOUGH_CREDITS_MESSAGE = (
    "❌ <b>Not enough credits</b>\n\n"
    "You need <b>{required}</b> credits but only have <b>{available}</b>.\n\n"
    "Top up your balance below:"
)

PAYMENT_METHOD_MESSAGE = (
    "💳 <b>Choose Payment Method</b>\n\n"
    "Item: <b>{item_name}</b>\n"
    "Price: <b>{price}</b>\n\n"
    "Select how you want to pay:"
)

PAYMENT_SUCCESS_STARS = (
    "✅ <b>Payment Successful!</b>\n\n"
    "Item: <b>{item_name}</b>\n"
    "Credits added: <b>+{credits_added}</b>\n"
    "Your new balance: <b>{new_balance}</b>\n\n"
    "Thank you for your purchase! 🎉"
)

PAYMENT_SUCCESS_STRIPE = (
    "✅ <b>Payment Successful!</b>\n\n"
    "Your payment has been processed.\n"
    "Credits will be added to your account shortly.\n\n"
    "Thank you for your purchase! 🎉"
)

PAYMENT_FAILED_MESSAGE = (
    "❌ <b>Payment Failed</b>\n\n"
    "Something went wrong with your payment. "
    "No credits have been deducted.\n\n"
    "Please try again or contact support."
)
