"""
Background removal service.

Primary provider: Remove.bg API
Fallback provider: ClipDrop API
"""

import logging
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"
CLIPDROP_URL = "https://clipdrop-api.co/remove-background/v1"


async def remove_background_removebg(image_path: str | Path, output_path: str | Path) -> str:
    """
    Remove background using Remove.bg API.

    Args:
        image_path: Local path to image
        output_path: Where to save the result (PNG with transparency)

    Returns:
        Path to the image with transparent background
    """
    if not settings.remove_bg_api_key:
        raise RuntimeError("Remove.bg API key not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(image_path, "rb") as image_file:
            response = await client.post(
                REMOVE_BG_URL,
                files={"image_file": image_file},
                data={"size": "auto"},
                headers={"X-Api-Key": settings.remove_bg_api_key},
            )

    if response.status_code != 200:
        logger.error("Remove.bg failed: %s - %s", response.status_code, response.text)
        raise RuntimeError(f"Remove.bg error: {response.status_code}")

    with open(output_path, "wb") as out:
        out.write(response.content)

    logger.info("Background removed via Remove.bg: %s", output_path)
    return str(output_path)


async def remove_background_clipdrop(image_path: str | Path, output_path: str | Path) -> str:
    """
    Remove background using ClipDrop API (fallback).

    Args:
        image_path: Local path to image
        output_path: Where to save the result

    Returns:
        Path to the image with transparent background
    """
    if not settings.clipdrop_api_key:
        raise RuntimeError("ClipDrop API key not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(image_path, "rb") as image_file:
            response = await client.post(
                CLIPDROP_URL,
                files={"image_file": image_file.read()},
                headers={"x-api-key": settings.clipdrop_api_key},
            )

    if response.status_code != 200:
        logger.error("ClipDrop failed: %s - %s", response.status_code, response.text)
        raise RuntimeError(f"ClipDrop error: {response.status_code}")

    with open(output_path, "wb") as out:
        out.write(response.content)

    logger.info("Background removed via ClipDrop: %s", output_path)
    return str(output_path)


async def remove_background(image_path: str | Path, output_path: str | Path) -> str:
    """
    Remove background using primary provider with automatic fallback.

    Priority:
      1. Remove.bg
      2. ClipDrop

    Args:
        image_path: Source image path
        output_path: Destination path

    Returns:
        Path to image with transparent background
    """
    # Try Remove.bg first
    if settings.remove_bg_api_key:
        try:
            return await remove_background_removebg(image_path, output_path)
        except Exception as e:
            logger.warning("Remove.bg failed, trying fallback: %s", e)

    # Fallback to ClipDrop
    if settings.clipdrop_api_key:
        try:
            return await remove_background_clipdrop(image_path, output_path)
        except Exception as e:
            logger.error("ClipDrop fallback also failed: %s", e)
            raise RuntimeError("All background removal providers failed") from e

    raise RuntimeError("No background removal API keys configured")
