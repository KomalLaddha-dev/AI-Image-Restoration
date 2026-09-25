"""
Stage 3: Face Restoration using GFPGAN v1.4.
Detects and restores degraded faces in the image while preserving identity.
Falls back to CodeFormer for severe degradation (stretch).
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import torch
from loguru import logger

from app.config import get_settings
from app.utils.image_utils import detect_faces


class FaceRestoreStage:
    """GFPGAN v1.4 face restoration."""

    name = "face_restore"

    def __init__(self):
        self._restorer = None
        self._loaded = False

    def load(self) -> None:
        """Lazy-load the GFPGAN model."""
        if self._loaded:
            return

        settings = get_settings()
        try:
            # Patch for basicsr which expects an older torchvision structure
            import torchvision.transforms.functional
            import sys
            if 'torchvision.transforms.functional_tensor' not in sys.modules:
                sys.modules['torchvision.transforms.functional_tensor'] = torchvision.transforms.functional

            from gfpgan import GFPGANer

            model_path = Path(settings.model_dir) / "GFPGANv1.4.pth"

            self._restorer = GFPGANer(
                model_path=str(model_path) if model_path.exists() else "GFPGANv1.4.pth",
                upscale=2,  # Face upscale factor
                arch="clean",  # Architecture: 'clean' for v1.4
                channel_multiplier=2,
                bg_upsampler=None,  # We handle background upscaling separately (Stage 5)
                device=torch.device(settings.device),
            )
            self._loaded = True
            logger.info("GFPGAN v1.4 model loaded successfully")

        except ImportError as e:
            logger.warning(f"GFPGAN not available: {e}. Face restore stage will be skipped.")
            self._loaded = False

    def is_available(self) -> bool:
        return self._loaded and self._restorer is not None

    async def process(self, img: np.ndarray) -> np.ndarray:
        """
        Restore faces in a BGR image using GFPGAN.
        Skips processing if no faces are detected.
        """
        start = time.perf_counter()

        # Quick face detection check — skip if no faces found
        faces = detect_faces(img)
        if not faces:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"Face restore: no faces detected, skipping ({elapsed:.0f}ms)")
            return img

        if not self.is_available():
            self.load()

        if not self.is_available():
            logger.warning("GFPGAN unavailable, returning original image")
            return img

        try:
            # GFPGAN returns: (cropped_faces, restored_faces, restored_img)
            _, _, output = self._restorer.enhance(
                img,
                has_aligned=False,  # Input has not been face-aligned
                only_center_face=False,  # Process all detected faces
                paste_back=True,  # Paste restored faces back into original image
                weight=0.5,  # Blending weight (0=original, 1=restored)
            )

            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                f"Face restore (GFPGAN): {len(faces)} face(s) restored in {elapsed:.0f}ms"
            )
            return output

        except Exception as e:
            logger.error(f"GFPGAN failed: {e}")
            return img

    def unload(self) -> None:
        """Free model memory."""
        if self._restorer is not None:
            del self._restorer
            self._restorer = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("GFPGAN model unloaded")
