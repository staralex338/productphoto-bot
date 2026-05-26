"""
Upscale service — enhances generated images using Real-ESRGAN via Fal.ai.

Costs 1 credit per upscale.
"""

import logging
from pathlib import Path

from aiogram import Bot

from app.bot.i18n import Translator
from app.bot.keyboards import generation_result_keyboard
from app.bot.services.fal_client import upscale_image
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.database.repositories import GenerationRepository, UserRepository
from app.utils.image import resize_image
from app.utils.storage import upload_image

logger = logging.getLogger(__name__)
settings = get_settings()

TEMP_DIR = Path("/tmp/productphoto_bot/upscales")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


async def run_upscale(
    generation_id: int,
    telegram_id: int,
    chat_id: int,
    bot: Bot,
) -> None:
    """
    Upscale the first image of a generation.

    Pipeline:
      1. Fetch original generation
      2. Download first generated image
      3. Run Real-ESRGAN upscale via Fal.ai
      4. Upload result to Supabase
      5. Send to user
    """
    logger.info("Starting upscale for generation %s", generation_id)

    # Fetch user language
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        lang = user.language if user else "en"
    t = Translator(lang)

    try:
        # -----------------------------------------------------------------
        # Step 1: Fetch generation
        # -----------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            gen_repo = GenerationRepository(session)
            generation = await gen_repo.get_by_id(generation_id)

            if not generation or generation.status != "completed":
                await bot.send_message(
                    chat_id=chat_id,
                    text=t.t("upscale_error_not_found"),
                )
                return

            # Get first image URL
            image_urls = generation.generated_image_url.split(",")
            if not image_urls:
                await bot.send_message(
                    chat_id=chat_id,
                    text=t.t("upscale_error_no_images"),
                )
                return

            source_url = image_urls[0]

        # -----------------------------------------------------------------
        # Step 2: Download source image
        # -----------------------------------------------------------------
        import httpx

        local_path = TEMP_DIR / f"upscale_{generation_id}_source.jpg"
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(response.content)

        # -----------------------------------------------------------------
        # Step 3: Upscale via Fal.ai
        # -----------------------------------------------------------------
        upscaled_url = await upscale_image(str(local_path), scale=2)

        # Download upscaled result
        upscaled_local = TEMP_DIR / f"upscale_{generation_id}_result.jpg"
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(upscaled_url)
            response.raise_for_status()
            with open(upscaled_local, "wb") as f:
                f.write(response.content)

        # -----------------------------------------------------------------
        # Step 4: Upload to Supabase
        # -----------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            db_user_id = user.id if user else telegram_id

        remote_path = f"user_{db_user_id}/upscale_{generation_id}.jpg"
        storage_url = await upload_image(str(upscaled_local), remote_path)

        # -----------------------------------------------------------------
        # Step 5: Send result to user
        # -----------------------------------------------------------------
        from aiogram.types import FSInputFile

        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(str(upscaled_local)),
            caption=t.t("upscale_complete"),
            reply_markup=generation_result_keyboard(generation_id, lang),
        )

        logger.info("Upscale for generation %s completed", generation_id)

    except Exception as e:
        logger.exception("Upscale for generation %s failed: %s", generation_id, e)

        # Refund credit on failure
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user:
                await user_repo.add_credits(user.id, 1)

        await bot.send_message(
            chat_id=chat_id,
            text=t.t("generation_error"),
            reply_markup=generation_result_keyboard(generation_id, lang),
        )

    finally:
        # Cleanup
        for path in TEMP_DIR.glob(f"upscale_{generation_id}_*"):
            try:
                path.unlink()
            except OSError:
                pass
