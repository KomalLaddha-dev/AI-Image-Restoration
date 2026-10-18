"""
Download pretrained model weights for all restoration pipeline stages.

Usage:
    cd backend
    python scripts/download_models.py

Downloads to the `models/` directory and sets up Bringing-Old-Photos-Back-to-Life.
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
from pathlib import Path

from loguru import logger


MODELS = {
    "RealESRGAN_x4plus.pth": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "size_mb": 67,
        "description": "Real-ESRGAN x4 upscaler (Stage 5)",
    },
    "GFPGANv1.4.pth": {
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
        "size_mb": 348,
        "description": "GFPGAN v1.4 face restoration (Stage 4)",
    },
    "ddcolor_modelscope.pth": {
        "url": "https://huggingface.co/piddnad/DDColor-models/resolve/main/ddcolor_modelscope.pth",
        "size_mb": 331,
        "description": "DDColor colorization model (Stage 3)",
    },
    "NAFNet-SIDD-width64.pth": {
        "url": "https://huggingface.co/nyanko7/nafnet-models/resolve/main/NAFNet-SIDD-width64.pth",
        "size_mb": 464,
        "description": "NAFNet SIDD denoising model",
    },
}

BOPBTL_CHECKPOINTS_URL = "https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life/releases/download/v1.0/global_checkpoints.zip"


def download_file(url: str, dest: Path, description: str = "") -> bool:
    """Download a file with progress reporting."""
    if dest.exists() and dest.stat().st_size > 1024 * 1024:
        logger.info(f"✓ Already exists: {dest.name} ({description})")
        return True

    logger.info(f"⬇ Downloading: {dest.name} ({description})...")
    try:
        def progress_hook(count, block_size, total_size):
            if total_size > 0:
                percent = min(100, count * block_size * 100 // total_size)
                sys.stdout.write(f"\r  Progress: {percent}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, str(dest), reporthook=progress_hook)
        print()  # newline after progress
        logger.info(f"✓ Downloaded: {dest.name}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to download {dest.name}: {e}")
        return False


def setup_bopbtl(backend_dir: Path) -> bool:
    """Ensure Bringing-Old-Photos-Back-to-Life repository and checkpoints exist."""
    bopbtl_dir = backend_dir / "Bringing-Old-Photos-Back-to-Life"
    global_dir = bopbtl_dir / "Global"
    checkpoints_dir = global_dir / "checkpoints"
    detection_ckpt = checkpoints_dir / "detection" / "FT_Epoch_latest.pt"

    if detection_ckpt.exists():
        logger.info("✓ Bringing-Old-Photos-Back-to-Life checkpoints already present.")
        return True

    logger.info("Setting up Bringing-Old-Photos-Back-to-Life...")

    if not bopbtl_dir.exists():
        logger.info("Cloning Bringing-Old-Photos-Back-to-Life repository...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life"],
                cwd=str(backend_dir),
                check=True
            )
        except Exception as e:
            logger.error(f"Failed to clone BOPBTL: {e}")
            return False

    # Download global_checkpoints.zip
    zip_dest = backend_dir / "global_checkpoints.zip"
    if not zip_dest.exists() or zip_dest.stat().st_size < 1024 * 1024:
        logger.info("Downloading BOPBTL global_checkpoints.zip (~800MB)...")
        if not download_file(BOPBTL_CHECKPOINTS_URL, zip_dest, "BOPBTL global checkpoints"):
            return False

    # Extract to Global/checkpoints
    logger.info("Extracting global_checkpoints.zip...")
    try:
        with zipfile.ZipFile(zip_dest, "r") as z:
            z.extractall(str(global_dir))
        logger.info("✓ BOPBTL checkpoints extracted successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to extract global_checkpoints.zip: {e}")
        return False


def main():
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    model_dir = backend_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading model checkpoints to: {model_dir}")
    print("=" * 60)

    # 1. Download PyTorch models
    success_count = 0
    for filename, info in MODELS.items():
        dest = model_dir / filename
        if download_file(info["url"], dest, info["description"]):
            success_count += 1

    print("\n" + "=" * 60)
    logger.info(f"Model downloads: {success_count}/{len(MODELS)} verified.")

    # 2. Setup BOPBTL
    setup_bopbtl(backend_dir)

    print("\n" + "=" * 60)
    logger.info("✅ All models verified and ready!")
    logger.info("Start backend with:")
    logger.info("    uvicorn app.main:create_app --factory --reload --port 8000")


if __name__ == "__main__":
    main()
