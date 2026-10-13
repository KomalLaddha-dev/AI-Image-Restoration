"""
Stage 2: Denoise and Deblur using NAFNet.
Removes noise, blur, and JPEG compression artifacts.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import torch
from loguru import logger

from app.config import get_settings


class DenoiseDeblurStage:
    """NAFNet-based denoising and deblurring."""

    name = "denoise"

    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Lazy-load the NAFNet model."""
        if self._loaded:
            return

        settings = get_settings()
        model_path = Path(settings.model_dir) / "NAFNet-SIDD-width64.pth"

        try:
            if model_path.exists():
                # Load local NAFNet architecture file
                from app.ml.stages.nafnet_arch import NAFNet as NAFNetArch

                self._model = NAFNetArch(
                    img_channel=3,
                    width=64,
                    middle_blk_num=12,
                    enc_blk_nums=[2, 2, 4, 8],
                    dec_blk_nums=[2, 2, 2, 2],
                )
                state_dict = torch.load(str(model_path), map_location=settings.device)
                if "params" in state_dict:
                    state_dict = state_dict["params"]
                self._model.load_state_dict(state_dict, strict=True)
                self._model.eval()
                self._model.to(settings.device)
                self._loaded = True
                logger.info("NAFNet denoising model loaded successfully")
            else:
                logger.warning(f"NAFNet weights not found at {model_path}")
        except ImportError:
            logger.warning("NAFNet architecture not found in basicsr. Using OpenCV fallback.")
        except Exception as e:
            logger.warning(f"NAFNet load failed: {e}. Using OpenCV denoise fallback.")

    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    async def process(self, img: np.ndarray, denoise_strength: float = 0.0) -> np.ndarray:
        """
        Denoise and deblur a BGR image using NAFNet.
        Default denoise_strength is 0.0 (NAFNet OFF by default).
        If denoise_strength > 0, blends: out = s * denoised + (1 - s) * input.
        """
        if denoise_strength <= 0.0:
            logger.info("Denoise: denoise_strength is 0.0, bypassing NAFNet to preserve texture")
            return img

        start = time.perf_counter()

        if not self.is_available():
            self.load()

        if self.is_available():
            try:
                denoised = self._run_nafnet(img)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"Denoise (NAFNet): completed in {elapsed:.0f}ms (strength={denoise_strength})")
                
                # Formula: out = s * denoised + (1 - s) * input
                if denoise_strength >= 1.0:
                    return denoised
                output = cv2.addWeighted(denoised, float(denoise_strength), img, float(1.0 - denoise_strength), 0.0)
                return output
            except Exception as e:
                logger.error(f"NAFNet inference failed: {e}")
                raise RuntimeError("NAFNet failed and OpenCV fallback is disabled.") from e
        else:
            raise RuntimeError("NAFNet model is not available.")

    def _run_nafnet(self, img: np.ndarray) -> np.ndarray:
        """Run NAFNet inference."""
        settings = get_settings()
        device = torch.device(settings.device)

        h, w = img.shape[:2]

        # Pad to multiple of 64 for NAFNet
        pad_h = (64 - h % 64) % 64
        pad_w = (64 - w % 64) % 64
        img_padded = cv2.copyMakeBorder(
            img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )

        # Convert BGR → RGB, normalize to [0, 1], to tensor
        img_rgb = cv2.cvtColor(img_padded, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(img_rgb.astype(np.float32) / 255.0)
        tensor = tensor.permute(2, 0, 1).unsqueeze(0).to(device)

        with torch.no_grad():
            output = self._model(tensor)

        # Post-process: tensor → numpy → BGR, remove padding
        output = output.squeeze(0).cpu().clamp(0, 1).numpy()
        output = (output.transpose(1, 2, 0) * 255).astype(np.uint8)
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        output = output[:h, :w]  # Remove padding

        return output


    def unload(self) -> None:
        """Free model memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("NAFNet model unloaded")
