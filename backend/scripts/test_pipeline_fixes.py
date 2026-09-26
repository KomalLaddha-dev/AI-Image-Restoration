"""
Test script for the two pipeline fixes:

1. Channel-correlation color detection — must give the same
   classification (gray/sepia) regardless of noise level.
2. Pipeline reorder — colorize must run right after BOPBTL,
   before denoise.

Run from backend/:
    python scripts/test_pipeline_fixes.py
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import cv2
from loguru import logger
from app.utils.image_utils import is_grayscale_or_sepia


def make_sepia_image(h: int = 512, w: int = 768) -> np.ndarray:
    """Create a realistic sepia scan: grayscale scene with brown tint + grain."""
    rng = np.random.default_rng(0)
    # Grayscale scene with smooth gradients and structure
    gray = np.zeros((h, w), dtype=np.float64)
    # Sky gradient (top 40%)
    for y in range(int(h * 0.4)):
        gray[y, :] = 200 - (y / (h * 0.4)) * 60
    # Ground/structure (bottom 60%)
    for y in range(int(h * 0.4), h):
        gray[y, :] = 100 + rng.normal(0, 15, w)
    gray = np.clip(gray, 0, 255)

    # Apply sepia tone matrix (brown tint)
    r = np.clip(gray * 1.05 + 20, 0, 255)
    g = np.clip(gray * 0.85 + 10, 0, 255)
    b = np.clip(gray * 0.65, 0, 255)

    img = np.stack([b, g, r], axis=-1).astype(np.uint8)  # BGR
    return img


def add_grain(img: np.ndarray, sigma: float = 25.0) -> np.ndarray:
    """Add luminance grain (like film grain — hits all channels equally)."""
    rng = np.random.default_rng(7)
    noise = rng.normal(0, sigma, img.shape[:2]).astype(np.float64)
    noisy = img.astype(np.float64)
    for c in range(3):
        noisy[:, :, c] += noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def make_color_image(h: int = 512, w: int = 768) -> np.ndarray:
    """Create an image with genuinely different hues (sky blue, green grass, red roof)."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    third = h // 3
    # Sky (blue)
    img[:third, :] = (200, 150, 80)       # BGR
    # Grass (green)
    img[third:2*third, :] = (50, 160, 60)  # BGR
    # Roof (red/brown)
    img[2*third:, :] = (40, 60, 180)       # BGR
    return img


def test_channel_correlation_stability():
    """
    Core test: the same sepia image must be classified identically
    before and after denoising (simulated by Gaussian blur).
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Channel-correlation stability across noise levels")
    logger.info("=" * 60)

    sepia_clean = make_sepia_image()
    sepia_noisy = add_grain(sepia_clean, sigma=30.0)
    # Simulate "after NAFNet denoising" with a Gaussian blur
    sepia_denoised = cv2.GaussianBlur(sepia_noisy, (0, 0), sigmaX=3.0)

    color_img = make_color_image()
    color_noisy = add_grain(color_img, sigma=30.0)

    tests = [
        ("Sepia (clean)",         sepia_clean),
        ("Sepia (noisy σ=30)",    sepia_noisy),
        ("Sepia (denoised)",      sepia_denoised),
        ("Color (clean)",         color_img),
        ("Color (noisy σ=30)",    color_noisy),
    ]

    results = {}
    for label, img in tests:
        needs_color, corr = is_grayscale_or_sepia(img)
        classification = "gray/sepia" if needs_color else "color"
        results[label] = (needs_color, corr)
        logger.info(f"  {label:30s} -> channel_corr={corr:.4f}  -> {classification}")

    # Verify stability: all three sepia variants must agree
    sepia_results = [results[k][0] for k in results if k.startswith("Sepia")]
    assert all(sepia_results), (
        f"FAIL: Sepia images classified inconsistently: "
        f"{[(k, results[k]) for k in results if k.startswith('Sepia')]}"
    )

    # Verify color images are NOT classified as gray/sepia
    color_results = [results[k][0] for k in results if k.startswith("Color")]
    assert not any(color_results), (
        f"FAIL: Color images misclassified as gray/sepia: "
        f"{[(k, results[k]) for k in results if k.startswith('Color')]}"
    )

    logger.info("  ✅ All sepia variants classified consistently as gray/sepia")
    logger.info("  ✅ All color variants classified consistently as color")


def test_pipeline_order():
    """Verify the new STAGE_ORDER in the pipeline."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 2: Pipeline stage order")
    logger.info("=" * 60)

    from app.ml.pipeline import RestorationPipeline
    from app.models.schemas import RestorationStage

    expected = [
        RestorationStage.OLD_PHOTO_REPAIR,
        RestorationStage.COLORIZE,
        RestorationStage.DENOISE,
        RestorationStage.FACE_RESTORE,
        RestorationStage.UPSCALE,
    ]

    actual = RestorationPipeline.STAGE_ORDER

    order_str = " → ".join(s.value for s in actual)
    logger.info(f"  Pipeline order: {order_str}")

    assert actual == expected, (
        f"FAIL: Expected order {[s.value for s in expected]}, "
        f"got {[s.value for s in actual]}"
    )
    logger.info("  ✅ Pipeline order is correct: old_photo_repair → colorize → denoise → face_restore → upscale")


if __name__ == "__main__":
    test_channel_correlation_stability()
    test_pipeline_order()
    logger.info("")
    logger.info("All tests passed.")
