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
from app.utils.image_utils import is_grayscale_or_sepia


class ColorizeStage:
    """DDColor-based B/W → Color conversion."""

    name = "colorize"

    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Lazy-load the DDColor model. Caches on first call; subsequent calls are no-ops."""
        if self._loaded:
            return

        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks
            logger.info("Initializing ModelScope DDColor pipeline...")
            
            # ModelScope caches weights in ~/.cache/modelscope/ — first call
            # downloads, subsequent calls load from cache.
            self._model = pipeline(Tasks.image_colorization, model='damo/cv_ddcolor_image-colorization')
            
            # Move to GPU if available for faster inference
            settings = get_settings()
            if settings.device == "cuda" and torch.cuda.is_available():
                if hasattr(self._model, 'model') and hasattr(self._model.model, 'to'):
                    self._model.model.to('cuda')
                    logger.info("DDColor model moved to CUDA")
            
            self._loaded = True
            device_name = "cuda" if settings.device == "cuda" and torch.cuda.is_available() else "cpu"
            logger.info(f"DDColor model loaded successfully via ModelScope (device={device_name})")
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            logger.warning(f"DDColor load failed: {e}\n{trace}")

    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    async def process(self, img: np.ndarray, colorization_mode: str = "auto") -> np.ndarray:
        """
        Colorize a BGR image using DDColor.

        Args:
            img: Input BGR image (NumPy array).
            colorization_mode: "auto", "force", or "off".

        Returns:
            Colorized BGR image.
        """
        start = time.perf_counter()

        if colorization_mode == "off":
            logger.info("Colorize: mode is off, skipping")
            return img

        # Determine if we should colorize — uses inter-channel correlation
        # (corr ≈ 1.0 = gray/sepia, corr < 0.92 = real color)
        needs_color, channel_corr = is_grayscale_or_sepia(img)
        
        logger.info(
            f"Colorize: mode={colorization_mode}, channel_corr={channel_corr:.4f}, "
            f"detected={'gray/sepia' if needs_color else 'color'}"
        )

        if colorization_mode == "auto" and not needs_color:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"Colorize: image is already color (auto mode), skipping ({elapsed:.0f}ms)")
            return img

        if not self.is_available():
            self.load()

        if self.is_available():
            try:
                output = self._run_ddcolor(img)
                elapsed = (time.perf_counter() - start) * 1000
                device_name = "cuda" if "cuda" in str(get_settings().device) else "cpu"
                logger.info(f"Colorize (DDColor): executed=True, device={device_name}, completed in {elapsed:.0f}ms")
                return output
            except Exception as e:
                logger.error(f"DDColor inference failed: {e}")
                raise RuntimeError(f"Colorization failed: {e}")

        logger.error("DDColor model is not available. Cannot perform colorization.")
        raise RuntimeError("DDColor model is not available.")

    def _run_ddcolor(self, img: np.ndarray) -> np.ndarray:
        """Run DDColor inference using ModelScope pipeline."""
        from modelscope.outputs import OutputKeys
        
        # ModelScope pipeline handles the resizing, L channel extraction, 
        # color inference, and LAB to BGR conversion internally.
        result = self._model(img)
        
        # The output is directly the colorized BGR image
        colorized = result[OutputKeys.OUTPUT_IMG]
        
        return colorized



    def unload(self) -> None:
        """Free model memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("DDColor model unloaded")
