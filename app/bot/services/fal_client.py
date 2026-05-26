"""
Fal.ai API client for image generation.

Uses fal_client library wrapped in asyncio.to_thread for async execution.
Supports:
  - Flux Schnell (fast, FREE/STARTER plans)
  - Flux Dev (premium quality, PRO plan)
  - Image-to-Image for product photography
"""

import asyncio
import base64
import logging
from pathlib import Path

import fal_client

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Model endpoints
MODELS = {
    "flux_schnell": "fal-ai/flux/schnell",
    "flux_dev": "fal-ai/flux/dev",
    "flux_dev_img2img": "fal-ai/flux/dev/image-to-image",
    "real_esrgan": "fal-ai/esrgan",
}


def _encode_image(image_path: str | Path) -> str:
    """Encode an image file to base64 data URI."""
    with open(image_path, "rb") as f:
        data = f.read()
    ext = Path(image_path).suffix.lstrip(".").replace("jpg", "jpeg")
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"


async def generate_image(
    prompt: str,
    model: str = "flux_schnell",
    image_path: str | Path | None = None,
    strength: float = 0.75,
    num_inference_steps: int = 28,
    guidance_scale: float = 7.5,
    negative_prompt: str = "",
    seed: int | None = None,
    num_images: int = 1,
) -> list[str]:
    """
    Generate image(s) using Fal.ai.

    Args:
        prompt: Text prompt describing the desired image
        model: Model key (flux_schnell, flux_dev, etc.)
        image_path: For img2img — path to source image
        strength: How much to modify source image (0-1)
        num_inference_steps: Number of denoising steps
        guidance_scale: Prompt adherence (CFG scale)
        negative_prompt: What to avoid
        seed: Random seed for reproducibility
        num_images: Number of images to generate

    Returns:
        List of URLs to generated images
    """
    endpoint = MODELS.get(model, model)
    arguments = {
        "prompt": prompt,
        "num_images": num_images,
        "enable_safety_checker": False,
    }

    if negative_prompt:
        arguments["negative_prompt"] = negative_prompt

    if seed is not None:
        arguments["seed"] = seed

    # Image-to-image parameters
    if image_path:
        arguments["image_url"] = _encode_image(image_path)
        arguments["strength"] = strength
        if "image-to-image" in endpoint:
            arguments["num_inference_steps"] = num_inference_steps
            arguments["guidance_scale"] = guidance_scale

    logger.info(
        "Calling Fal.ai endpoint=%s model=%s strength=%s images=%s",
        endpoint, model, strength, num_images,
    )

    try:
        # Run synchronous fal_client in thread pool to avoid blocking event loop
        result = await asyncio.to_thread(
            fal_client.run,
            endpoint,
            arguments=arguments,
        )

        # Extract image URLs from result
        images = []
        if isinstance(result, dict):
            if "images" in result:
                images = [img["url"] for img in result["images"]]
            elif "image" in result:
                images = [result["image"]["url"]]
            else:
                logger.warning("Unexpected Fal.ai response keys: %s", list(result.keys()))
        elif hasattr(result, "images"):
            images = [img["url"] for img in result.images]
        elif hasattr(result, "image"):
            images = [result.image["url"]]

        logger.info("Fal.ai generated %d images", len(images))
        return images

    except Exception as e:
        logger.exception("Fal.ai generation failed: %s", e)
        raise


async def upscale_image(image_path: str | Path, scale: int = 2) -> str:
    """
    Upscale an image using Real-ESRGAN via Fal.ai.

    Args:
        image_path: Path to image file
        scale: Upscaling factor (2 or 4)

    Returns:
        URL of upscaled image
    """
    arguments = {
        "image_url": _encode_image(image_path),
        "scale": scale,
    }

    logger.info("Upscaling image with Real-ESRGAN scale=%s", scale)

    try:
        result = await asyncio.to_thread(
            fal_client.run,
            MODELS["real_esrgan"],
            arguments=arguments,
        )

        if isinstance(result, dict):
            return result["image"]["url"]
        elif hasattr(result, "image"):
            return result.image["url"]
        else:
            raise RuntimeError(f"Unexpected upscale response: {result}")

    except Exception as e:
        logger.exception("Upscale failed: %s", e)
        raise
