"""
Stage 5: Image Super-Resolution using Real-ESRGAN.
Upscales images by 4x with robust handling of real-world degradation.
This is the most stable, pip-installable stage — integrated first.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import torch
from loguru import logger

from app.config import get_settings


class UpscaleStage:
    """Real-ESRGAN x4plus super-resolution."""

    name = "upscale"

    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Lazy-load the Real-ESRGAN model."""
        if self._loaded:
            return

        settings = get_settings()
        try:
            # Patch for basicsr which expects an older torchvision structure
            import torchvision.transforms.functional
            import sys
            if 'torchvision.transforms.functional_tensor' not in sys.modules:
                sys.modules['torchvision.transforms.functional_tensor'] = torchvision.transforms.functional

            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            # RRDBNet architecture for RealESRGAN_x4plus
            rrdb_model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4,
            )

            model_path = Path(settings.model_dir) / "RealESRGAN_x4plus.pth"

            self._model = RealESRGANer(
                scale=4,
                model_path=str(model_path) if model_path.exists() else None,
                model=rrdb_model,
                tile=400,  # Process in 400x400 chunks to prevent CPU OOM
                tile_pad=10,
                pre_pad=0,
                half=False,  # fp16 only on GPU
                device=settings.device,
            )
            self._loaded = True
            logger.info("Real-ESRGAN x4plus model loaded successfully")

        except ImportError as e:
            logger.warning(f"Real-ESRGAN not available: {e}. Upscale stage will use fallback.")
            self._loaded = False

    def is_available(self) -> bool:
        """Check if the model is loaded and ready."""
        return self._loaded and self._model is not None

    async def process(self, img: np.ndarray) -> np.ndarray:
        """
        Upscale a BGR image by 4x using Real-ESRGAN.
        Falls back to bicubic interpolation if the model isn't available.
        """
        start = time.perf_counter()

        if not self.is_available():
            self.load()

        if self.is_available():
            try:
                output, _ = self._model.enhance(img, outscale=4)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(
                    f"Upscale (Real-ESRGAN): {img.shape[1]}x{img.shape[0]} → "
                    f"{output.shape[1]}x{output.shape[0]} in {elapsed:.0f}ms"
                )
                return output
            except Exception as e:
                logger.error(f"Real-ESRGAN failed, falling back to bicubic: {e}")

        # Fallback: bicubic 4x upscale
        h, w = img.shape[:2]
        output = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Upscale (fallback bicubic): {w}x{h} → {w*4}x{h*4} in {elapsed:.0f}ms")
        return output

    def unload(self) -> None:
        """Free model memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Real-ESRGAN model unloaded")
