"""
Main generation service.

Orchestrates the full AI pipeline:
  1. Remove background from uploaded product photo
  2. Generate professional backgrounds using Fal.ai
  3. Download generated images
  4. Apply watermark for free users
  5. Upload to Supabase Storage
  6. Update database record
  7. Send results to user via Telegram
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot
from aiogram.types import BufferedInputFile, FSInputFile

from app.bot.keyboards import generation_result_keyboard
from app.bot.messages import GENERATION_ERROR_MESSAGE
from app.bot.services.background_removal import remove_background
from app.bot.services.fal_client import generate_image
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import GenerationRepository, UserRepository
from app.prompts.templates import get_style
from app.utils.image import add_watermark
from app.utils.storage import upload_image

logger = logging.getLogger(__name__)
settings = get_settings()

# Temporary directory for generation artifacts
TEMP_DIR = Path("/tmp/productphoto_bot/generations")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


async def run_generation(
    generation_id: int,
    photo_path: str,
    style_key: str,
    model: str,
    user_id: int,
    telegram_id: int,
    chat_id: int,
    bot: Bot,
) -> None:
    """
    Execute the full generation pipeline asynchronously.

    Args:
        generation_id: Database generation record ID
        photo_path: Local path to uploaded product photo
        style_key: Generation style key
        model: AI model to use (flux_schnell / flux_dev)
        user_id: Database user ID (for storage paths)
        telegram_id: Telegram user ID (for lookup)
        chat_id: Telegram chat ID to send results
        bot: aiogram Bot instance
    """
    logger.info("Starting generation %s for user %s", generation_id, user_id)

    try:
        # -----------------------------------------------------------------
        # Step 1: Remove background
        # -----------------------------------------------------------------
        no_bg_path = TEMP_DIR / f"{generation_id}_nobg.png"
        await remove_background(photo_path, no_bg_path)
        logger.info("Background removed for generation %s", generation_id)

        # -----------------------------------------------------------------
        # Step 2: Generate images via Fal.ai
        # -----------------------------------------------------------------
        style = get_style(style_key)
        num_images = settings.default_generations_count  # 2-4 images

        # Use different seeds for variety
        images_urls = await generate_image(
            prompt=style.prompt,
            model=model,
            image_path=str(no_bg_path),
            strength=style.strength,
            num_inference_steps=style.num_inference_steps,
            guidance_scale=style.guidance_scale,
            negative_prompt=style.negative_prompt,
            num_images=num_images,
        )

        if not images_urls:
            raise RuntimeError("Fal.ai returned no images")

        logger.info("Generated %d images for generation %s", len(images_urls), generation_id)

        # -----------------------------------------------------------------
        # Step 3: Download generated images
        # -----------------------------------------------------------------
        downloaded_paths = await _download_images(images_urls, generation_id)

        # -----------------------------------------------------------------
        # Step 4: Check if user is free (needs watermark)
        # -----------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            is_free = user.is_free if user else True
            db_user_id = user.id if user else user_id

        if is_free:
            for path in downloaded_paths:
                add_watermark(path, path)
            logger.info("Watermarks applied for free user %s", telegram_id)

        # -----------------------------------------------------------------
        # Step 5: Upload to Supabase Storage
        # -----------------------------------------------------------------
        storage_urls = []
        for idx, local_path in enumerate(downloaded_paths):
            remote_path = f"user_{db_user_id}/gen_{generation_id}_{idx}.jpg"
            url = await upload_image(local_path, remote_path)
            storage_urls.append(url)

        # -----------------------------------------------------------------
        # Step 6: Update database
        # -----------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            gen_repo = GenerationRepository(session)
            await gen_repo.update_status(
                generation_id=generation_id,
                status="completed",
                generated_image_url=",".join(storage_urls),
            )

        # -----------------------------------------------------------------
        # Step 7: Send results to user
        # -----------------------------------------------------------------
        await _send_results(bot, chat_id, downloaded_paths, generation_id, style.display_name)

        logger.info("Generation %s completed successfully", generation_id)

        return {
            "generation_id": generation_id,
            "status": "completed",
            "images": storage_urls,
            "style": style.display_name,
        }

    except Exception as e:
        logger.exception("Generation %s failed: %s", generation_id, e)

        # Refund credits on failure
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user:
                await user_repo.add_credits(user.id, 1)  # Refund 1 credit

            gen_repo = GenerationRepository(session)
            await gen_repo.update_status(
                generation_id=generation_id,
                status="failed",
                error_message=str(e),
            )

        # Notify user of failure
        await bot.send_message(
            chat_id=chat_id,
            text=GENERATION_ERROR_MESSAGE,
            reply_markup=generation_result_keyboard(generation_id),
        )

        return {
            "generation_id": generation_id,
            "status": "failed",
            "error": str(e),
        }

    finally:
        # Cleanup temp files
        _cleanup_generation_files(generation_id)


async def _download_images(urls: list[str], generation_id: int) -> list[str]:
    """Download generated images from URLs to local temp files."""
    import httpx

    paths = []
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for idx, url in enumerate(urls):
            response = await client.get(url)
            response.raise_for_status()

            path = TEMP_DIR / f"{generation_id}_gen_{idx}.jpg"
            with open(path, "wb") as f:
                f.write(response.content)
            paths.append(str(path))

    return paths


async def _send_results(
    bot: Bot,
    chat_id: int,
    image_paths: list[str],
    generation_id: int,
    style_name: str,
) -> None:
    """Send generated images as a media group to the user."""
    from aiogram.types import InputMediaPhoto

    media = [
        InputMediaPhoto(media=FSInputFile(path), caption=f"🎨 {style_name}" if i == 0 else "")
        for i, path in enumerate(image_paths)
    ]

    # Send as media group (up to 10 images)
    await bot.send_media_group(chat_id=chat_id, media=media)

    # Send action buttons below
    await bot.send_message(
        chat_id=chat_id,
        text="✅ Generation complete! What would you like to do next?",
        reply_markup=generation_result_keyboard(generation_id),
    )


def _cleanup_generation_files(generation_id: int) -> None:
    """Remove temporary files for a generation."""
    for path in TEMP_DIR.glob(f"{generation_id}_*"):
        try:
            path.unlink()
        except OSError:
            pass
