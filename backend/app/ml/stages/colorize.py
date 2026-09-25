"""
Stage 4: Image Colorization using DDColor.
Converts grayscale/B&W images to realistic color.
Falls back to DeOldify "vivid" mode as an alternative.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import torch
from loguru import logger

from app.config import get_settings
from app.utils.image_utils import is_grayscale


class ColorizeStage:
    """DDColor-based B/W → Color conversion."""

    name = "colorize"

    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Lazy-load the DDColor model."""
        if self._loaded:
            return

        settings = get_settings()
        model_path = Path(settings.model_dir) / "ddcolor_modelscope.pth"

        try:
            # DDColor uses a custom architecture — we load via torch directly
            if model_path.exists():
                self._model = torch.jit.load(str(model_path), map_location=settings.device)
                self._model.eval()
                self._loaded = True
                logger.info("DDColor model loaded successfully")
            else:
                logger.warning(
                    f"DDColor weights not found at {model_path}. "
                    "Colorize will use a simple LAB-space heuristic fallback."
                )
        except Exception as e:
            logger.warning(f"DDColor load failed: {e}. Using fallback colorization.")

    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    async def process(self, img: np.ndarray, force: bool = False) -> np.ndarray:
        """
        Colorize a BGR image.

        Args:
            img: Input BGR image (NumPy array).
            force: If True, colorize even if image appears to already be color.

        Returns:
            Colorized BGR image.
        """
        start = time.perf_counter()

        # Skip if the image is already in color (unless forced)
        if not force and not is_grayscale(img):
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"Colorize: image is already color, skipping ({elapsed:.0f}ms)")
            return img

        if not self.is_available():
            self.load()

        if self.is_available():
            try:
                output = self._run_ddcolor(img)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"Colorize (DDColor): completed in {elapsed:.0f}ms")
                return output
            except Exception as e:
                logger.error(f"DDColor inference failed: {e}")

        # Fallback: simple LAB-space pseudo-colorization (sepia-tinted)
        output = self._fallback_colorize(img)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Colorize (fallback sepia): completed in {elapsed:.0f}ms")
        return output

    def _run_ddcolor(self, img: np.ndarray) -> np.ndarray:
        """Run DDColor inference."""
        settings = get_settings()
        device = torch.device(settings.device)

        # Prepare input: resize to 512x512, normalize
        h, w = img.shape[:2]
        img_resized = cv2.resize(img, (512, 512), interpolation=cv2.INTER_CUBIC)

        # Convert to LAB, take L channel
        lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Normalize L to [0, 1] and create tensor
        l_tensor = torch.from_numpy(l_channel.astype(np.float32) / 255.0)
        l_tensor = l_tensor.unsqueeze(0).unsqueeze(0).to(device)  # (1, 1, 512, 512)

        with torch.no_grad():
            ab_pred = self._model(l_tensor)  # Predicted a, b channels

        # Post-process: denormalize and merge with L
        ab_pred = ab_pred.squeeze(0).cpu().numpy().transpose(1, 2, 0)  # (512, 512, 2)
        ab_pred = (ab_pred * 128).astype(np.float32)  # Scale to LAB range

        # Merge L + predicted ab
        lab_output = np.zeros((512, 512, 3), dtype=np.float32)
        lab_output[:, :, 0] = l_channel.astype(np.float32)
        lab_output[:, :, 1:] = ab_pred

        # Convert back to BGR and resize to original dimensions
        colorized = cv2.cvtColor(lab_output.astype(np.uint8), cv2.COLOR_LAB2BGR)
        colorized = cv2.resize(colorized, (w, h), interpolation=cv2.INTER_CUBIC)

        return colorized

    def _fallback_colorize(self, img: np.ndarray) -> np.ndarray:
        """
        Simple fallback: apply a warm sepia tone to grayscale images.
        This is not ML-based — just a visually pleasing tint.
        """
        # Ensure grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply sepia color map
        normalized = gray.astype(np.float64) / 255.0
        sepia = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.float64)
        sepia[:, :, 0] = normalized * 204  # B
        sepia[:, :, 1] = normalized * 204  # G
        sepia[:, :, 2] = normalized * 230  # R (warmer)

        return np.clip(sepia, 0, 255).astype(np.uint8)

    def unload(self) -> None:
        """Free model memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("DDColor model unloaded")
