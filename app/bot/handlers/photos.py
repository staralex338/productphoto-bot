"""
Photo upload handler.

Validates uploaded images and transitions user to style selection state.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from PIL import Image

from app.bot.keyboards import style_selection_keyboard
from app.bot.messages import ASK_UPLOAD_MESSAGE, INVALID_PHOTO_MESSAGE, PHOTO_RECEIVED_MESSAGE
from app.bot.services.storage import download_telegram_photo
from app.bot.states import GenerationFlow
from app.config import get_settings

logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


async def validate_image(file_path: str) -> tuple[bool, str]:
    """
    Validate an image file.

    Checks:
      - File size <= max allowed
      - Format is supported (JPG, PNG, WEBP)
      - Dimensions >= minimum required

    Returns:
        (is_valid, error_message)
    """
    import os

    # Check file size
    size_bytes = os.path.getsize(file_path)
    if size_bytes > settings.max_image_size_bytes:
        max_mb = settings.max_image_size_mb
        return False, f"Image too large ({size_bytes / 1024 / 1024:.1f} MB). Max: {max_mb} MB."

    # Check format and dimensions
    try:
        with Image.open(file_path) as img:
            if img.format not in ("JPEG", "PNG", "WEBP"):
                return False, f"Unsupported format: {img.format}. Use JPG, PNG, or WEBP."

            width, height = img.size
            if width < settings.min_image_dimension or height < settings.min_image_dimension:
                min_dim = settings.min_image_dimension
                return False, f"Image too small ({width}×{height}). Minimum: {min_dim}×{min_dim}px."

            return True, ""
    except Exception as e:
        logger.error("Image validation error: %s", e)
        return False, "Could not read image file. Please try another image."


@router.message(F.photo)
async def on_photo_received(message: Message, state: FSMContext, bot: Bot):
    """
    Handle product photo upload.

    1. Download the largest available photo
    2. Validate size, format, dimensions
    3. Store file path in FSM state
    4. Ask user to choose a style
    """
    # Get the highest resolution photo (last in the list)
    photo = message.photo[-1]

    # Download file
    file_path = await download_telegram_photo(bot, photo, prefix="upload")

    # Validate
    is_valid, error = await validate_image(str(file_path))
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n{ASK_UPLOAD_MESSAGE}",
        )
        return

    # Store in state for the next step
    await state.update_data(
        uploaded_photo_path=str(file_path),
        original_file_id=photo.file_id,
    )
    await state.set_state(GenerationFlow.choosing_style)

    await message.answer(
        PHOTO_RECEIVED_MESSAGE,
        reply_markup=style_selection_keyboard(),
    )


@router.message(F.document)
async def on_document_received(message: Message, state: FSMContext, bot: Bot):
    """
    Handle image sent as document (e.g., WEBP or uncompressed PNG).

    Some users send images as files to avoid Telegram compression.
    """
    document = message.document

    # Check mime type
    if document.mime_type not in ("image/jpeg", "image/png", "image/webp"):
        await message.answer(INVALID_PHOTO_MESSAGE)
        return

    # Download
    from app.bot.services.storage import download_telegram_document
    file_path = await download_telegram_document(
        bot, document.file_id, document.file_name
    )

    # Validate
    is_valid, error = await validate_image(str(file_path))
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n{ASK_UPLOAD_MESSAGE}",
        )
        return

    # Store in state
    await state.update_data(
        uploaded_photo_path=str(file_path),
        original_file_id=document.file_id,
    )
    await state.set_state(GenerationFlow.choosing_style)

    await message.answer(
        PHOTO_RECEIVED_MESSAGE,
        reply_markup=style_selection_keyboard(),
    )
