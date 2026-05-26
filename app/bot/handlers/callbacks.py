"""
Callback query handlers for inline keyboards.

Handles style selection, generation triggers, and action buttons.
"""

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.keyboards import generation_result_keyboard, main_menu_keyboard
from app.bot.messages import (
    ASK_UPLOAD_MESSAGE,
    GENERATION_ERROR_MESSAGE,
    GENERATION_STARTED_MESSAGE,
    NOT_ENOUGH_CREDITS_MESSAGE,
)
from app.bot.states import GenerationFlow
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import GenerationRepository, UserRepository

logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()

# Map callback data to human-readable style names
STYLE_NAMES = {
    "white_background": "⚪ White Background",
    "lifestyle": "🏠 Lifestyle",
    "studio_premium": "💎 Studio Premium",
    "social_media_ad": "📱 Social Media Ad",
}


# =============================================================================
# Style Selection
# =============================================================================

@router.callback_query(F.data.startswith("style:"))
async def on_style_selected(callback: CallbackQuery, state: FSMContext):
    """
    Handle style selection from inline keyboard.

    1. Extract style from callback data
    2. Check user has enough credits
    3. Deduct credits and create generation record
    4. Trigger async generation task
    5. Show "generating..." message
    """
    style_key = callback.data.split(":")[1]
    style_name = STYLE_NAMES.get(style_key, style_key)

    # Get uploaded photo from state
    data = await state.get_data()
    photo_path = data.get("uploaded_photo_path")
    original_file_id = data.get("original_file_id")

    if not photo_path:
        await callback.answer("Session expired. Please upload a photo again.", show_alert=True)
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("Please send /start first.", show_alert=True)
            return

        # Check credits (1 credit per generation)
        credits_needed = 1
        if user.credits < credits_needed:
            await callback.message.edit_text(
                NOT_ENOUGH_CREDITS_MESSAGE.format(
                    required=credits_needed,
                    available=user.credits,
                ),
                reply_markup=main_menu_keyboard(),
            )
            await callback.answer()
            return

        # Deduct credits atomically
        success = await user_repo.deduct_credits(user.id, credits_needed)
        if not success:
            await callback.answer("Could not deduct credits. Try again.", show_alert=True)
            return

        # Determine model based on subscription
        model = "flux_dev" if user.subscription_type == "pro" else "flux_schnell"

        # Create generation record
        # TODO STEP 4: Replace with actual Supabase Storage URL after upload
        temp_original_url = f"file://{photo_path}"

        gen_repo = GenerationRepository(session)
        generation = await gen_repo.create(
            user_id=user.id,
            original_image_url=temp_original_url,
            generation_type=style_key,
            model_used=model,
            credits_spent=credits_needed,
        )

        # Update state
        await state.set_state(GenerationFlow.generating)
        await state.update_data(
            generation_id=generation.id,
            style=style_key,
        )

    # Send generating message
    await callback.message.edit_text(
        GENERATION_STARTED_MESSAGE.format(style=style_name),
    )
    await callback.answer(f"Generating {style_name}...")

    # Submit generation to task queue (non-blocking, with concurrency control)
    from app.bot.services.generator import run_generation
    from app.bot.services.task_queue import get_task_queue

    queue = get_task_queue()
    await queue.submit(
        task_id=f"gen_{generation.id}",
        task_type="generation",
        user_id=callback.from_user.id,
        coro_factory=lambda: run_generation(
            generation_id=generation.id,
            photo_path=photo_path,
            style_key=style_key,
            model=model,
            user_id=user.id,
            telegram_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            bot=callback.bot,
        ),
    )
    logger.info("Generation %s submitted to task queue", generation.id)


# =============================================================================
# Generation Actions (Regenerate / Upscale)
# =============================================================================

@router.callback_query(F.data.startswith("action:regenerate:"))
async def on_regenerate(callback: CallbackQuery, state: FSMContext):
    """
    Handle regenerate button click.

    Fetches the original generation and restarts with the same parameters.
    """
    generation_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        gen_repo = GenerationRepository(session)
        user_repo = UserRepository(session)

        original = await gen_repo.get_by_id(generation_id)
        if not original:
            await callback.answer("Generation not found.", show_alert=True)
            return

        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Please send /start first.", show_alert=True)
            return

        # Check credits
        if user.credits < 1:
            await callback.answer("Not enough credits!", show_alert=True)
            return

        # Deduct credits
        success = await user_repo.deduct_credits(user.id, 1)
        if not success:
            await callback.answer("Could not deduct credits.", show_alert=True)
            return

        # Create new generation record
        new_gen = await gen_repo.create(
            user_id=user.id,
            original_image_url=original.original_image_url,
            generation_type=original.generation_type,
            model_used=original.model_used,
            credits_spent=1,
        )

    # Submit regenerate to task queue
    from app.bot.services.generator import run_generation
    from app.bot.services.task_queue import get_task_queue

    queue = get_task_queue()
    await queue.submit(
        task_id=f"gen_{new_gen.id}",
        task_type="generation",
        user_id=callback.from_user.id,
        coro_factory=lambda: run_generation(
            generation_id=new_gen.id,
            photo_path=original.original_image_url.replace("file://", ""),
            style_key=original.generation_type,
            model=original.model_used,
            user_id=user.id,
            telegram_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            bot=callback.bot,
        ),
    )

    style_name = STYLE_NAMES.get(original.generation_type, original.generation_type)
    await callback.message.answer(
        GENERATION_STARTED_MESSAGE.format(style=style_name),
    )
    await callback.answer("Regenerating...")


@router.callback_query(F.data.startswith("action:upscale:"))
async def on_upscale(callback: CallbackQuery, state: FSMContext):
    """
    Handle upscale button click.

    Deducts 1 credit and submits upscale to task queue.
    """
    generation_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("Please send /start first.", show_alert=True)
            return

        if user.credits < 1:
            await callback.answer("Not enough credits for upscale!", show_alert=True)
            return

        # Deduct credit
        success = await user_repo.deduct_credits(user.id, 1)
        if not success:
            await callback.answer("Could not deduct credits.", show_alert=True)
            return

    # Submit upscale to task queue
    from app.bot.services.upscaler import run_upscale
    from app.bot.services.task_queue import get_task_queue

    queue = get_task_queue()
    await queue.submit(
        task_id=f"upscale_{generation_id}",
        task_type="upscale",
        user_id=callback.from_user.id,
        coro_factory=lambda: run_upscale(
            generation_id=generation_id,
            telegram_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            bot=callback.bot,
        ),
    )

    await callback.answer("Upscaling...")
    await callback.message.answer("🔍 <b>Upscale started!</b>\n\nThis will take a few seconds...")


# =============================================================================
# Buy Menu
# =============================================================================

@router.callback_query(F.data == "menu:buy")
async def on_menu_buy(callback: CallbackQuery):
    """Show buy credits menu."""
    from app.bot.keyboards import buy_credits_keyboard
    from app.bot.messages import PAYMENT_CHOOSE_MESSAGE

    await callback.message.edit_text(
        PAYMENT_CHOOSE_MESSAGE,
        reply_markup=buy_credits_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def on_buy_item(callback: CallbackQuery):
    """
    Handle purchase selection.

    Shows payment method selection (Stars or Stripe).
    """
    parts = callback.data.split(":")
    item_type = parts[1]  # subscription | pack
    item_name = parts[2]  # starter | pro | 50 | 100 | 500

    from app.bot.keyboards import payment_method_keyboard
    from app.bot.messages import PAYMENT_METHOD_MESSAGE
    from app.payments.credits import get_price_display

    price = get_price_display(item_type, item_name, currency="stars")

    if item_type == "subscription":
        display_name = f"{item_name.title()} Plan"
    else:
        display_name = f"{item_name} Credits Pack"

    await callback.message.edit_text(
        PAYMENT_METHOD_MESSAGE.format(
            item_name=display_name,
            price=price,
        ),
        reply_markup=payment_method_keyboard(item_type, item_name),
    )
    await callback.answer()


# =============================================================================
# Payment Method Selection
# =============================================================================

@router.callback_query(F.data.startswith("pay:stars:"))
async def on_pay_with_stars(callback: CallbackQuery):
    """Handle Telegram Stars payment selection."""
    parts = callback.data.split(":")
    item_type = parts[2]
    item_name = parts[3]

    from app.payments.telegram_stars import (
        send_credit_pack_invoice,
        send_subscription_invoice,
    )

    if item_type == "subscription":
        await send_subscription_invoice(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            plan=item_name,
        )
    elif item_type == "pack":
        await send_credit_pack_invoice(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            pack_size=item_name,
        )

    await callback.answer()


@router.callback_query(F.data.startswith("pay:stripe:"))
async def on_pay_with_stripe(callback: CallbackQuery):
    """Handle Stripe payment selection."""
    parts = callback.data.split(":")
    item_type = parts[2]
    item_name = parts[3]

    from app.payments.stripe_client import (
        create_credit_pack_session,
        create_subscription_session,
    )

    success_url = f"https://t.me/{(await callback.bot.get_me()).username}"
    cancel_url = success_url

    try:
        if item_type == "subscription":
            url = await create_subscription_session(
                telegram_id=callback.from_user.id,
                plan=item_name,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        elif item_type == "pack":
            url = await create_credit_pack_session(
                telegram_id=callback.from_user.id,
                pack_size=item_name,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        else:
            await callback.answer("Unknown item type", show_alert=True)
            return

        await callback.message.answer(
            f"💳 <b>Complete your payment</b>\n\n"
            f"Click the link below to pay securely via Stripe:\n"
            f"<a href='{url}'>Pay Now</a>\n\n"
            f"After payment, your credits will be added automatically.",
        )
        await callback.answer()

    except Exception as e:
        logger.exception("Stripe payment error: %s", e)
        await callback.answer("Payment setup failed. Try again.", show_alert=True)


# =============================================================================
# Generate Flow Entry
# =============================================================================

@router.callback_query(F.data == "menu:generate")
async def on_menu_generate(callback: CallbackQuery, state: FSMContext):
    """Start the generation flow from main menu."""
    await state.set_state(GenerationFlow.uploading)
    await callback.message.edit_text(ASK_UPLOAD_MESSAGE)
    await callback.answer("Send me a product photo!")
