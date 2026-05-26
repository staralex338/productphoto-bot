"""
Photo upload handler.

Validates uploaded images and transitions user to style selection state.
Supports multilingual messages.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from PIL import Image

from app.bot.i18n import Translator
from app.bot.keyboards import style_selection_keyboard
from app.bot.services.storage import download_telegram_photo
from app.bot.states import GenerationFlow
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import UserRepository

logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


async def validate_image(file_path: str, t: Translator = None) -> tuple[bool, str]:
    """
    Validate an image file.

    Checks:
      - File size <= max allowed
      - Format is supported (JPG, PNG, WEBP)
      - Dimensions >= minimum required

    Args:
        file_path: Path to the image file
        t: Optional Translator for localized error messages

    Returns:
        (is_valid, error_message)
    """
    import os

    _t = t or Translator("en")

    # Check file size
    size_bytes = os.path.getsize(file_path)
    if size_bytes > settings.max_image_size_bytes:
        max_mb = settings.max_image_size_mb
        return False, _t.t("image_too_large", size=size_bytes / 1024 / 1024, max_mb=max_mb)

    # Check format and dimensions
    try:
        with Image.open(file_path) as img:
            if img.format not in ("JPEG", "PNG", "WEBP"):
                return False, _t.t("unsupported_format", format=img.format)

            width, height = img.size
            if width < settings.min_image_dimension or height < settings.min_image_dimension:
                min_dim = settings.min_image_dimension
                return False, _t.t("image_too_small", width=width, height=height, min_dim=min_dim)

            return True, ""
    except Exception as e:
        logger.error("Image validation error: %s", e)
        return False, _t.t("could_not_read_image")


async def get_user_language(telegram_id: int) -> str:
    """Fetch user's preferred language from database."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        return user.language if user else "en"


@router.message(F.photo)
async def on_photo_received(message: Message, state: FSMContext, bot: Bot):
    """
    Handle product photo upload.

    1. Download the largest available photo
    2. Validate size, format, dimensions
    3. Store file path in FSM state
    4. Ask user to choose a style
    """
    lang = await get_user_language(message.from_user.id)
    t = Translator(lang)

    # Get the highest resolution photo (last in the list)
    photo = message.photo[-1]

    # Download file
    file_path = await download_telegram_photo(bot, photo, prefix="upload")

    # Validate
    is_valid, error = await validate_image(str(file_path), t)
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n{t.t('ask_upload', max_size=settings.max_image_size_mb, min_dim=settings.min_image_dimension)}",
        )
        return

    # Store in state for the next step
    await state.update_data(
        uploaded_photo_path=str(file_path),
        original_file_id=photo.file_id,
    )
    await state.set_state(GenerationFlow.choosing_style)

    await message.answer(
        t.t("photo_received"),
        reply_markup=style_selection_keyboard(lang),
    )


@router.message(F.document)
async def on_document_received(message: Message, state: FSMContext, bot: Bot):
    """
    Handle image sent as document (e.g., WEBP or uncompressed PNG).

    Some users send images as files to avoid Telegram compression.
    """
    lang = await get_user_language(message.from_user.id)
    t = Translator(lang)

    document = message.document

    # Check mime type
    if document.mime_type not in ("image/jpeg", "image/png", "image/webp"):
        await message.answer(t.t("invalid_photo", max_size=settings.max_image_size_mb, min_dim=settings.min_image_dimension))
        return

    # Download
    from app.bot.services.storage import download_telegram_document
    file_path = await download_telegram_document(
        bot, document.file_id, document.file_name
    )

    # Validate
    is_valid, error = await validate_image(str(file_path), t)
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n{t.t('ask_upload', max_size=settings.max_image_size_mb, min_dim=settings.min_image_dimension)}",
        )
        return

    # Store in state
    await state.update_data(
        uploaded_photo_path=str(file_path),
        original_file_id=document.file_id,
    )
    await state.set_state(GenerationFlow.choosing_style)

    await message.answer(
        t.t("photo_received"),
        reply_markup=style_selection_keyboard(lang),
    )
