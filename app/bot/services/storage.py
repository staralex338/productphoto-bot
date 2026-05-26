"""
Simple file download service for Telegram bot.

Downloads images from Telegram servers to temporary local storage.
In production, files are uploaded to Supabase Storage after processing.
"""

import logging
import os
from pathlib import Path

from aiogram import Bot
from aiogram.types import PhotoSize

logger = logging.getLogger(__name__)

# Temporary directory for downloaded files
TEMP_DIR = Path("/tmp/productphoto_bot")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


async def download_telegram_photo(
    bot: Bot,
    photo: PhotoSize,
    prefix: str = "product",
) -> Path:
    """
    Download a photo from Telegram servers.

    Args:
        bot: aiogram Bot instance
        photo: PhotoSize object from message
        prefix: Filename prefix for identification

    Returns:
        Path to the downloaded file
    """
    # Telegram file IDs don't have extensions, so we add .jpg
    filename = f"{prefix}_{photo.file_unique_id}.jpg"
    destination = TEMP_DIR / filename

    await bot.download(file=photo.file_id, destination=destination)
    logger.info("Downloaded photo to %s (size: %s bytes)", destination, destination.stat().st_size)

    return destination


async def download_telegram_document(
    bot: Bot,
    file_id: str,
    file_name: str | None = None,
) -> Path:
    """
    Download a document (e.g., WEBP image) from Telegram.

    Args:
        bot: aiogram Bot instance
        file_id: Telegram file_id
        file_name: Original filename (optional)

    Returns:
        Path to the downloaded file
    """
    if file_name:
        filename = file_name.replace(" ", "_")
    else:
        filename = f"doc_{file_id}.bin"

    destination = TEMP_DIR / filename
    await bot.download(file=file_id, destination=destination)
    logger.info("Downloaded document to %s", destination)

    return destination


def cleanup_temp_file(path: Path) -> None:
    """Remove a temporary file if it exists."""
    try:
        if path.exists():
            path.unlink()
            logger.debug("Cleaned up temp file: %s", path)
    except OSError as e:
        logger.warning("Failed to cleanup temp file %s: %s", path, e)
