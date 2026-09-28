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
import torch

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

    async def process(self, img: np.ndarray, max_bopbtl_size: int = 768, use_hr_mode: bool = False) -> np.ndarray:
        """
        Run the Microsoft BOPBTL Global restoration stage via subprocess.
        """
        start = time.perf_counter()

        if not self.is_available():
            self.load()

        settings = get_settings()
        cuda_available = torch.cuda.is_available()
        
        if settings.device == "cuda" and not cuda_available:
            raise RuntimeError("GPU mode requested for BOPBTL but CUDA is not available!")
            
        gpu_id = "0" if cuda_available and settings.device == "cuda" else "-1"
        device_str = "CPU" if gpu_id == "-1" else "GPU 0"
        gpu_name = torch.cuda.get_device_name(0) if gpu_id != "-1" else "N/A"
        
        h_orig, w_orig = img.shape[:2]
        
        from app.utils.image_utils import resize_if_needed
        img, scale = resize_if_needed(img, max_side=max_bopbtl_size)
        h_in, w_in = img.shape[:2]
        if scale < 1.0:
            logger.info(f"BOPBTL: Downscaled input from {w_orig}x{h_orig} to {w_in}x{h_in} (max_side={max_bopbtl_size})")

        # Config option to test --HR true vs false
        hr_flag = "--HR" if use_hr_mode else ""

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
            logger.info(f"BOPBTL: Running scratch detection on {device_str}...")
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

            if cuda_available:
                torch.cuda.empty_cache()

            # 2. Restoration (Scratch and Quality restore)
            logger.info(f"BOPBTL: Running restoration on {device_str} (HR={use_hr_mode})...")
            cmd2 = f'"{python_exe}" test.py --Scratch_and_Quality_restore --test_input "{new_input}" --test_mask "{new_mask}" --outputs_dir "{output_dir}" --gpu_ids {gpu_id} {hr_flag}'
            
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

            # Read the final output image
            restored_dir = output_dir / "restored_image"
            output_files = list(restored_dir.glob("*")) if restored_dir.exists() else []

            # If GPU ran out of memory, retry on GPU with a smaller image before CPU fallback
            if not output_files and gpu_id != "-1":
                oom_downscale = 768
                logger.warning(f"BOPBTL GPU OOM at {w_in}x{h_in}. Retrying on GPU with max_side={oom_downscale}...")

                # Downscale the input and mask for a second GPU attempt
                oom_input_dir = temp_dir_path / "oom_input"
                oom_mask_dir = temp_dir_path / "oom_mask"
                oom_output_dir = temp_dir_path / "oom_output"
                oom_input_dir.mkdir()
                oom_mask_dir.mkdir()
                oom_output_dir.mkdir()

                # Re-read, resize, and re-detect at smaller scale
                small_img, _ = resize_if_needed(img, max_side=oom_downscale)
                h_small, w_small = small_img.shape[:2]
                cv2.imwrite(str(oom_input_dir / "image.png"), small_img)

                cmd1_small = f'"{python_exe}" detection.py --test_path "{oom_input_dir}" --output_dir "{oom_mask_dir}" --input_size full_size --GPU {gpu_id}'
                await asyncio.to_thread(
                    subprocess.run, cmd1_small,
                    cwd=str(self._global_dir), shell=True, capture_output=True, text=True
                )
                oom_new_input = oom_mask_dir / "input"
                oom_new_mask = oom_mask_dir / "mask"

                cmd2_small = f'"{python_exe}" test.py --Scratch_and_Quality_restore --test_input "{oom_new_input}" --test_mask "{oom_new_mask}" --outputs_dir "{oom_output_dir}" --gpu_ids {gpu_id} {hr_flag}'
                proc2_small = await asyncio.to_thread(
                    subprocess.run, cmd2_small,
                    cwd=str(self._global_dir), shell=True, capture_output=True, text=True
                )
                logger.debug(f"BOPBTL retry STDOUT: {proc2_small.stdout}")

                oom_restored_dir = oom_output_dir / "restored_image"
                oom_files = list(oom_restored_dir.glob("*")) if oom_restored_dir.exists() else []

                if oom_files:
                    logger.info(f"BOPBTL: GPU retry succeeded at {w_small}x{h_small}")
                    restored_dir = oom_restored_dir
                    output_files = oom_files
                    w_in, h_in = w_small, h_small  # update for logging
                else:
                    # Final fallback: CPU at the reduced resolution
                    logger.warning("BOPBTL GPU retry also failed. Falling back to CPU...")
                    cmd2_cpu = f'"{python_exe}" test.py --Scratch_and_Quality_restore --test_input "{oom_new_input}" --test_mask "{oom_new_mask}" --outputs_dir "{oom_output_dir}" --gpu_ids -1 {hr_flag}'
                    await asyncio.to_thread(
                        subprocess.run, cmd2_cpu,
                        cwd=str(self._global_dir), shell=True, capture_output=True, text=True
                    )
                    oom_files = list(oom_restored_dir.glob("*")) if oom_restored_dir.exists() else []
                    if oom_files:
                        restored_dir = oom_restored_dir
                        output_files = oom_files
                        device_str = "CPU (fallback)"
                        w_in, h_in = w_small, h_small

            if not restored_dir.exists() or not output_files:
                raise RuntimeError("BOPBTL did not produce any output images.")

            output_img_path = output_files[0]
            restored_img = cv2.imread(str(output_img_path))

            if restored_img is None:
                raise RuntimeError(f"Failed to read restored image from {output_img_path}")

            elapsed = (time.perf_counter() - start) * 1000
            h_out, w_out = restored_img.shape[:2]
            
            vram_str = "N/A"
            if gpu_id != "-1":
                try:
                    vram_str = f"{torch.cuda.memory_allocated(0)/(1024**2):.1f}MB"
                except:
                    pass
            
            # Log exact metrics per PRD
            logger.info(
                f"Stage: BOPBTL\n"
                f"  Device: {device_str}\n"
                f"  GPU name: {gpu_name}\n"
                f"  Input resolution: {w_in}x{h_in}\n"
                f"  Output resolution: {w_out}x{h_out}\n"
                f"  Processing time: {elapsed:.0f}ms\n"
                f"  VRAM if measurable: {vram_str}"
            )

            return restored_img

    def unload(self) -> None:
        """Free model memory (handled by subprocess exit automatically)."""
        self._loaded = False
        logger.info("BOPBTL stage unloaded")
