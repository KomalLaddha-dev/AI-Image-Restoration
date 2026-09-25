import os
import shutil
import time
import asyncio
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
import tempfile
import sys

from app.config import get_settings

class BOPBTLStage:
    """
    Stage 1: Old Photo Repair (Microsoft Bringing Old Photos Back to Life).
    Mandatory first stage that runs the official MS pretrained models via subprocess.
    """

    name = "old_photo_repair"

    def __init__(self):
        self._loaded = False
        self._repo_path = Path(__file__).parent.parent.parent.parent / "Bringing-Old-Photos-Back-to-Life"
        self._global_dir = self._repo_path / "Global"
        
        # Checkpoints to verify
        self._checkpoints = [
            self._global_dir / "checkpoints" / "restoration" / "mapping_quality",
            self._global_dir / "checkpoints" / "restoration" / "mapping_scratch",
            self._global_dir / "checkpoints" / "detection" / "FT_Epoch_latest.pt"
        ]

    def load(self) -> None:
        """Verify the repository and weights exist."""
        if self._loaded:
            return

        if not self._repo_path.exists():
            raise RuntimeError(f"BOPBTL repository not found at {self._repo_path}. Please clone the repository first.")

        # Check for weights
        for cp in self._checkpoints:
            if not cp.exists():
                raise RuntimeError(f"BOPBTL weights missing: {cp}. Please download global_checkpoints.zip and extract to {self._global_dir}/checkpoints/")

        self._loaded = True
        logger.info("Microsoft BOPBTL stage verified and loaded.")

    def is_available(self) -> bool:
        return self._loaded

    async def process(self, img: np.ndarray) -> np.ndarray:
        """
        Run the Microsoft BOPBTL Global restoration stage via subprocess.
        """
        start = time.perf_counter()

        if not self.is_available():
            self.load()

        # BOPBTL is extremely memory intensive on CPU for large images.
        # Downscale if the longest side exceeds 800 pixels.
        h, w = img.shape[:2]
        max_dim = 800
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            logger.info(f"BOPBTL: Resizing image from {w}x{h} to {new_w}x{new_h} to avoid OOM")
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        settings = get_settings()
        gpu_id = "0" if settings.device == "cuda" else "-1"

        # Create temporary directories for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_dir = temp_dir_path / "input"
            mask_dir = temp_dir_path / "mask"
            output_dir = temp_dir_path / "output"

            input_dir.mkdir()
            mask_dir.mkdir()
            output_dir.mkdir()

            # Save the input image
            input_img_path = input_dir / "image.png"
            cv2.imwrite(str(input_img_path), img)

            python_exe = sys.executable if sys.executable else "python"

            # 1. Detection (find scratches)
            logger.info("BOPBTL: Running scratch detection...")
            cmd1 = f'"{python_exe}" detection.py --test_path "{input_dir}" --output_dir "{mask_dir}" --input_size full_size --GPU {gpu_id}'
            
            import subprocess
            proc1 = await asyncio.to_thread(
                subprocess.run,
                cmd1,
                cwd=str(self._global_dir),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if proc1.returncode != 0:
                logger.error(f"BOPBTL Detection Failed:\nSTDOUT: {proc1.stdout}\nSTDERR: {proc1.stderr}")
                raise RuntimeError(f"BOPBTL detection stage failed with return code {proc1.returncode}")

            # The detection script creates 'input' and 'mask' subdirs in the mask_dir
            new_input = mask_dir / "input"
            new_mask = mask_dir / "mask"

            # 2. Restoration (Scratch and Quality restore)
            logger.info("BOPBTL: Running restoration...")
            cmd2 = f'"{python_exe}" test.py --Scratch_and_Quality_restore --test_input "{new_input}" --test_mask "{new_mask}" --outputs_dir "{output_dir}" --gpu_ids {gpu_id}'
            
            proc2 = await asyncio.to_thread(
                subprocess.run,
                cmd2,
                cwd=str(self._global_dir),
                shell=True,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"BOPBTL test.py STDOUT: {proc2.stdout}")
            if proc2.stderr:
                logger.debug(f"BOPBTL test.py STDERR: {proc2.stderr}")
            
            if proc2.returncode != 0:
                logger.error(f"BOPBTL Restore Failed:\nSTDOUT: {proc2.stdout}\nSTDERR: {proc2.stderr}")
                raise RuntimeError(f"BOPBTL restore stage failed with return code {proc2.returncode}")

            # Read the final output image
            restored_dir = output_dir / "restored_image"
            if not restored_dir.exists():
                raise RuntimeError("BOPBTL did not produce a restored_image directory.")

            output_files = list(restored_dir.glob("*"))
            if not output_files:
                raise RuntimeError("BOPBTL did not produce any output images.")

            output_img_path = output_files[0]
            restored_img = cv2.imread(str(output_img_path))

            if restored_img is None:
                raise RuntimeError(f"Failed to read restored image from {output_img_path}")

            elapsed = (time.perf_counter() - start) * 1000
            
            # Log exact metrics per PRD
            h_in, w_in = img.shape[:2]
            h_out, w_out = restored_img.shape[:2]
            device_str = "GPU" if gpu_id != "-1" else "CPU"
            
            logger.info(f"Stage: BOPBTL | Time: {elapsed:.0f}ms | Device: {device_str} | Input: {w_in}x{h_in} | Output: {w_out}x{h_out}")

            return restored_img

    def unload(self) -> None:
        """Free model memory (handled by subprocess exit automatically)."""
        self._loaded = False
        logger.info("BOPBTL stage unloaded")
