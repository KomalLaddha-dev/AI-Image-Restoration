import os
import cv2
import time
import asyncio
import numpy as np
import tempfile
import sys
import subprocess
from pathlib import Path
from loguru import logger
import torch
from app.config import get_settings
from app.utils.image_utils import resize_if_needed

class CrackInpaintStage:
    name = "crack_inpaint"

    def __init__(self):
        self._loaded = False
        self._repo_path = Path(__file__).parent.parent.parent.parent / "Bringing-Old-Photos-Back-to-Life"
        self._global_dir = self._repo_path / "Global"
        self._lama = None

    def load(self) -> None:
        if self._loaded:
            return

        try:
            from simple_lama_inpainting import SimpleLama
            self._lama = SimpleLama()
            logger.info("LaMa loaded for crack inpainting.")
        except ImportError:
            logger.warning("simple-lama-inpainting not installed. Falling back to cv2.inpaint (lower quality).")
        except Exception as e:
            logger.warning(f"Failed to load LaMa: {e}. Falling back to cv2.inpaint.")
            
        self._loaded = True

    def is_available(self) -> bool:
        return self._loaded

    async def process(self, img: np.ndarray, dilation_px: int = 5) -> np.ndarray:
        start = time.perf_counter()
        
        if not self.is_available():
            self.load()

        settings = get_settings()
        cuda_available = torch.cuda.is_available()
        gpu_id = "0" if cuda_available and settings.device == "cuda" else "-1"
        python_exe = sys.executable if sys.executable else "python"

        h_orig, w_orig = img.shape[:2]
        
        # 1. Resize to <=768 for mask detection
        small_img, scale = resize_if_needed(img, max_side=768)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_dir = temp_dir_path / "input"
            mask_dir = temp_dir_path / "mask"
            input_dir.mkdir()
            mask_dir.mkdir()

            cv2.imwrite(str(input_dir / "image.png"), small_img)

            # Detect scratches
            cmd = f'"{python_exe}" detection.py --test_path "{input_dir}" --output_dir "{mask_dir}" --input_size full_size --GPU {gpu_id}'
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=str(self._global_dir),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if proc.returncode != 0:
                logger.error("Scratch detection for inpainting failed.")
                return img
                
            new_mask = mask_dir / "mask"
            mask_files = list(new_mask.glob("*.png"))
            if not mask_files:
                logger.warning("No mask output from scratch detection.")
                return img
                
            mask = cv2.imread(str(mask_files[0]), cv2.IMREAD_GRAYSCALE)
            
            if mask is None:
                return img

        # Upsample mask to original resolution
        mask_up = cv2.resize(mask, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
        
        # Threshold
        _, mask_thresh = cv2.threshold(mask_up, 127, 255, cv2.THRESH_BINARY)
        
        # Dilate
        kernel = np.ones((dilation_px, dilation_px), np.uint8)
        mask_dilated = cv2.dilate(mask_thresh, kernel, iterations=1)
        
        # Coverage guard
        coverage = np.sum(mask_dilated > 0) / (h_orig * w_orig)
        logger.info(f"Crack mask coverage: {coverage*100:.2f}%")
        
        if coverage > 0.15:
            logger.warning(f"Mask coverage {coverage*100:.2f}% > 15%, skipping inpainting (likely fired on texture).")
            return img

        # Inpaint
        peak_vram = "N/A"
        try:
            if cuda_available and settings.device == "cuda":
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "reset_peak_memory_stats"):
                    torch.cuda.reset_peak_memory_stats()
            
            if self._lama is not None:
                from PIL import Image
                img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                mask_pil = Image.fromarray(mask_dilated)
                
                res_pil = await asyncio.to_thread(self._lama, img_pil, mask_pil)
                res = cv2.cvtColor(np.array(res_pil), cv2.COLOR_RGB2BGR)
                logger.info("Used LaMa for inpainting.")
            else:
                res = cv2.inpaint(img, mask_dilated, 3, cv2.INPAINT_TELEA)
                logger.info("Used cv2.inpaint (Telea) for inpainting (lower quality).")
                
            if cuda_available and settings.device == "cuda":
                if hasattr(torch.cuda, "max_memory_allocated"):
                    peak_vram = f"{torch.cuda.max_memory_allocated() / (1024**2):.1f}MB"
                
        except Exception as e:
            logger.error(f"Inpainting failed: {e}")
            res = img
            
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Stage: crack_inpaint | Time: {elapsed:.0f}ms | Peak VRAM: {peak_vram}")
        return res
        
    def unload(self):
        if self._lama is not None:
            del self._lama
            self._lama = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self._loaded = False
