"""
Supabase Storage utilities.

Uploads images to Supabase Storage and returns public URLs.
Images auto-expire after STORAGE_TTL_DAYS (30 days).
"""

import logging
from pathlib import Path

from supabase import create_client

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Supabase client
supabase = create_client(settings.supabase_url, settings.supabase_key)


async def upload_image(
    local_path: str | Path,
    remote_path: str,
    bucket: str | None = None,
) -> str:
    """
    Upload a local image file to Supabase Storage.

    Args:
        local_path: Path to local file
        remote_path: Destination path in bucket (e.g., "user_123/generation_456.jpg")
        bucket: Bucket name (default from settings)

    Returns:
        Public URL of the uploaded file
    """
    bucket = bucket or settings.supabase_storage_bucket
    local_path = Path(local_path)

    with open(local_path, "rb") as f:
        response = supabase.storage.from_(bucket).upload(
            path=remote_path,
            file=f.read(),
            file_options={"content-type": f"image/{local_path.suffix.lstrip('.').replace('jpg', 'jpeg')}"},
        )

    # Get public URL
    public_url = supabase.storage.from_(bucket).get_public_url(remote_path)
    logger.info("Uploaded image to %s", public_url)

    return public_url


async def delete_image(remote_path: str, bucket: str | None = None) -> None:
    """Delete an image from Supabase Storage."""
    bucket = bucket or settings.supabase_storage_bucket
    try:
        supabase.storage.from_(bucket).remove([remote_path])
        logger.info("Deleted image from storage: %s", remote_path)
    except Exception as e:
        logger.warning("Failed to delete image %s: %s", remote_path, e)
