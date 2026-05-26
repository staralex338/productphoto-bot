"""
Image processing utilities.

Handles watermarking, resizing, format conversion, and overlays.
Uses Pillow for all operations.
"""

import io
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Bot watermark text (displayed in corner for free users)
WATERMARK_TEXT = "ProductPhoto AI"
WATERMARK_FONT_SIZE = 24


def add_watermark(
    image_path: str | Path,
    output_path: str | Path | None = None,
    text: str = WATERMARK_TEXT,
) -> str:
    """
    Add a subtle watermark to an image.

    Args:
        image_path: Path to source image
        output_path: Where to save result (defaults to overwriting source)
        text: Watermark text

    Returns:
        Path to watermarked image
    """
    img = Image.open(image_path).convert("RGBA")

    # Create transparent overlay
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", WATERMARK_FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", WATERMARK_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

    # Text size and position (bottom-right corner with padding)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = 20
    position = (img.width - text_width - padding, img.height - text_height - padding)

    # Draw text with slight shadow for readability
    shadow_offset = 2
    draw.text(
        (position[0] + shadow_offset, position[1] + shadow_offset),
        text,
        font=font,
        fill=(0, 0, 0, 128),
    )
    draw.text(position, text, font=font, fill=(255, 255, 255, 180))

    # Composite overlay onto original
    watermarked = Image.alpha_composite(img, overlay)

    # Convert back to RGB if saving as JPEG
    if str(output_path).lower().endswith(".jpg") or str(output_path).lower().endswith(".jpeg"):
        watermarked = watermarked.convert("RGB")

    # Determine output path
    if output_path is None:
        output_path = image_path

    watermarked.save(output_path, quality=95)
    logger.info("Added watermark to %s", output_path)

    return str(output_path)


def resize_image(
    image_path: str | Path,
    max_dimension: int = 1024,
    output_path: str | Path | None = None,
) -> str:
    """
    Resize image to fit within max_dimension while maintaining aspect ratio.

    Args:
        image_path: Source image path
        max_dimension: Max width or height
        output_path: Output path (default: overwrite)

    Returns:
        Path to resized image
    """
    img = Image.open(image_path)

    if max(img.width, img.height) <= max_dimension:
        return str(image_path)

    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    if output_path is None:
        output_path = image_path

    img.save(output_path, quality=95)
    logger.info("Resized image to %dx%d", img.width, img.height)

    return str(output_path)


def image_to_bytes(image_path: str | Path, format: str = "PNG") -> bytes:
    """Load an image and convert to bytes buffer."""
    img = Image.open(image_path)
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def composite_product_on_background(
    product_path: str | Path,
    background_path: str | Path,
    output_path: str | Path,
) -> str:
    """
    Overlay a product (with transparent background) onto a generated background.

    This is used when we generate backgrounds separately and need to place
    the original product on top.
    """
    product = Image.open(product_path).convert("RGBA")
    background = Image.open(background_path).convert("RGBA")

    # Resize product to fit background if needed (max 80% of background)
    max_w = int(background.width * 0.8)
    max_h = int(background.height * 0.8)

    if product.width > max_w or product.height > max_h:
        product.thumbnail((max_w, max_h), Image.LANCZOS)

    # Center the product
    x = (background.width - product.width) // 2
    y = (background.height - product.height) // 2

    # Paste using alpha channel
    background.paste(product, (x, y), product)

    # Convert to RGB for JPEG
    result = background.convert("RGB")
    result.save(output_path, quality=95)
    logger.info("Composited product onto background: %s", output_path)

    return str(output_path)
