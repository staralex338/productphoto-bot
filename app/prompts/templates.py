"""
Prompt templates for AI image generation.

Each style defines:
  - prompt: the main generation prompt
  - negative_prompt: what to avoid (optional)
  - strength: how much to deviate from original (for img2img)

These prompts are optimized for Flux models via Fal.ai.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StyleTemplate:
    """Template for a generation style."""

    name: str
    display_name: str
    prompt: str
    negative_prompt: str
    strength: float = 0.75  # img2img strength (0-1)
    num_inference_steps: int = 28
    guidance_scale: float = 7.5


# =============================================================================
# Style Definitions
# =============================================================================

STYLES: dict[str, StyleTemplate] = {
    "white_background": StyleTemplate(
        name="white_background",
        display_name="⚪ White Background",
        prompt=(
            "Professional e-commerce product photography, the product placed centrally, "
            "pure seamless white background, soft realistic drop shadows beneath the product, "
            "studio lighting with softbox, clean minimal composition, high detail, "
            "catalog style, photorealistic, 8k uhd"
        ),
        negative_prompt=(
            "busy background, cluttered, people, hands, text, watermark, blurry, "
            "low quality, distorted, multiple products"
        ),
        strength=0.65,
    ),
    "lifestyle": StyleTemplate(
        name="lifestyle",
        display_name="🏠 Lifestyle",
        prompt=(
            "Premium lifestyle product photography, the product elegantly placed in a "
            "beautiful modern home interior scene, natural daylight streaming through windows, "
            "cozy warm atmosphere, shallow depth of field, bokeh background, "
            "commercial photography, photorealistic, 8k uhd"
        ),
        negative_prompt=(
            "white background, isolated product, studio backdrop, plain background, "
            "cartoon, illustration, blurry product, distorted, ugly"
        ),
        strength=0.75,
    ),
    "studio_premium": StyleTemplate(
        name="studio_premium",
        display_name="💎 Studio Premium",
        prompt=(
            "Luxury advertising photography, the product showcased with dramatic cinematic lighting, "
            "glossy reflective surfaces, dark elegant backdrop with subtle gradient, "
            "premium high-end feel, sharp focus, professional studio setup, "
            "gold and black tones, photorealistic, 8k uhd"
        ),
        negative_prompt=(
            "cheap look, plastic feel, flat lighting, overexposed, cluttered background, "
            "cartoon, illustration, people, text, watermark"
        ),
        strength=0.70,
    ),
    "social_media_ad": StyleTemplate(
        name="social_media_ad",
        display_name="📱 Social Media Ad",
        prompt=(
            "Viral social media product advertisement, the product featured in a bold "
            "bright colorful composition, trending modern aesthetic, eye-catching arrangement, "
            "vibrant saturated colors, dynamic angle, Instagram-worthy, commercial ad creative, "
            "photorealistic, 8k uhd"
        ),
        negative_prompt=(
            "boring composition, dull colors, plain white background, blurry, "
            "low quality, distorted, ugly, text, watermark"
        ),
        strength=0.80,
    ),
}


def get_style(style_key: str) -> StyleTemplate:
    """Get a style template by key."""
    if style_key not in STYLES:
        raise ValueError(f"Unknown style: {style_key}. Available: {list(STYLES.keys())}")
    return STYLES[style_key]


def list_styles() -> list[StyleTemplate]:
    """Return all available styles."""
    return list(STYLES.values())
