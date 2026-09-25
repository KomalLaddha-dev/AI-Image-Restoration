"""
Stage 1: Old Photo Repair — scratch, crease, and faded-patch removal.
Uses the "Bringing Old Photos Back to Life" approach.

For MVP, this stage uses a combination of:
1. Scratch/damage detection via simple thresholding
2. Inpainting damaged regions with OpenCV (Navier-Stokes / Telea)
3. Histogram equalization for faded patches

The full Microsoft BOPBTL model requires a more complex setup (VAE + mapping network).
We integrate it as a pluggable model when weights are available.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from app.config import get_settings


class OldPhotoRepairStage:
    """
    Old photo defect repair: scratches, creases, faded regions.
    MVP uses classical CV techniques; full model is a stretch goal.
    """

    name = "old_photo_repair"

    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Attempt to load the Bringing Old Photos Back to Life model."""
        settings = get_settings()
        model_path = Path(settings.model_dir) / "old_photo_repair"

        if model_path.exists() and (model_path / "vae.pth").exists():
            try:
                # TODO: Integrate full BOPBTL model when weights are available
                logger.info("Full old photo repair model found — loading...")
                self._loaded = True
            except Exception as e:
                logger.warning(f"Full model load failed: {e}. Using classical CV repair.")
        else:
            logger.info(
                "Old photo repair: using classical CV (scratch detect + inpaint). "
                "For better quality, add BOPBTL model weights to models/old_photo_repair/"
            )

    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    async def process(self, img: np.ndarray) -> np.ndarray:
        """
        Repair old photo defects.
        Pipeline: scratch detection → inpainting → fade correction.
        """
        start = time.perf_counter()

        # Step 1: Detect scratches and damage
        damage_mask = self._detect_damage(img)

        # Step 2: Inpaint damaged regions
        if damage_mask is not None and np.any(damage_mask > 0):
            img = self._inpaint(img, damage_mask)
            logger.debug("Inpainted damaged regions")

        # Step 3: Fix faded/low-contrast areas
        img = self._fix_fading(img)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Old photo repair (classical CV): completed in {elapsed:.0f}ms")
        return img

    def _detect_damage(self, img: np.ndarray) -> np.ndarray | None:
        """
        Detect scratches and creases using edge detection + morphological ops.
        Returns a binary mask of damaged regions.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        # High-pass filter to detect thin scratches
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        diff = cv2.absdiff(gray, blurred)

        # Threshold to get scratch-like features
        _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # Morphological close to connect nearby scratch segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Filter out very large regions (not scratches) and very small noise
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_mask = np.zeros_like(mask)
        img_area = img.shape[0] * img.shape[1]

        for contour in contours:
            area = cv2.contourArea(contour)
            # Keep contours that are scratch-shaped (elongated, not too large)
            if 50 < area < img_area * 0.05:
                x, y, w, h = cv2.boundingRect(contour)
                aspect = max(w, h) / (min(w, h) + 1e-6)
                if aspect > 3.0:  # Elongated = likely a scratch
                    cv2.drawContours(filtered_mask, [contour], -1, 255, -1)

        # Dilate mask slightly for better inpainting coverage
        kernel = np.ones((3, 3), np.uint8)
        filtered_mask = cv2.dilate(filtered_mask, kernel, iterations=2)

        return filtered_mask

    def _inpaint(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Inpaint damaged regions using OpenCV's Navier-Stokes method.
        Better for scratch-like damage than Telea.
        """
        return cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)

    def _fix_fading(self, img: np.ndarray) -> np.ndarray:
        """
        Correct faded/low-contrast images using CLAHE (Contrast Limited
        Adaptive Histogram Equalization). Works well for old photos
        that have lost dynamic range.
        """
        # Convert to LAB color space — equalize L channel only
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # CLAHE with moderate clip limit (avoids over-enhancement)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)

        # Merge back
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    def unload(self) -> None:
        """Free model memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False
            logger.info("Old photo repair model unloaded")
