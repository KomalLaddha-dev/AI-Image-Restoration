"""
Download pretrained model weights for all restoration pipeline stages.

Usage:
    python scripts/download_models.py

Downloads to the `models/` directory.
"""

import os
import sys
import urllib.request
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
        "description": "GFPGAN v1.4 face restoration (Stage 3)",
    },
    "ddcolor_modelscope.pth": {
        "url": "https://huggingface.co/piddnad/DDColor-models/resolve/main/ddcolor_modelscope.pth",
        "size_mb": 331,
        "description": "DDColor colorization model (Stage 4)",
    },
    "NAFNet-REDS-width64.pth": {
        "url": "https://huggingface.co/nyanko7/nafnet-models/resolve/main/NAFNet-REDS-width64.pth",
        "size_mb": 260,
        "description": "NAFNet denoising/deblur model (Stage 2)",
    },
}

# These models require manual download due to licensing or complex setup:
MANUAL_MODELS = {
    "Bringing-Old-Photos-Back-to-Life": {
        "source": "https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life",
        "instructions": "1. cd backend && git clone https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life\n      2. cd Bringing-Old-Photos-Back-to-Life && cd Face_Enhancement/models/networks && git clone https://github.com/vacancy/Synchronized-BatchNorm-PyTorch\n      3. cp -r Synchronized-BatchNorm-PyTorch/sync_batchnorm . && cd ../../../Global/detection_models && git clone https://github.com/vacancy/Synchronized-BatchNorm-PyTorch && cp -r Synchronized-BatchNorm-PyTorch/sync_batchnorm .\n      4. Download https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life/releases/download/v1.0/global_checkpoints.zip\n      5. Unzip to backend/Bringing-Old-Photos-Back-to-Life/Global/checkpoints",
        "description": "Microsoft BOPBTL Repository and Weights",
    }
}


def download_file(url: str, dest: Path, description: str = "") -> bool:
    """Download a file with progress reporting."""
    if dest.exists():
        logger.info(f"✓ Already exists: {dest.name} ({description})")
        return True

    logger.info(f"⬇ Downloading: {dest.name} ({description})...")
    try:
        def progress_hook(count, block_size, total_size):
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


def main():
    model_dir = Path("models")
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading models to: {model_dir.absolute()}")
    print("=" * 60)

    # Auto-downloadable models
    success_count = 0
    for filename, info in MODELS.items():
        dest = model_dir / filename
        if download_file(info["url"], dest, info["description"]):
            success_count += 1

    print("\n" + "=" * 60)
    logger.info(f"Auto-downloaded: {success_count}/{len(MODELS)} models")

    # Manual download instructions
    if MANUAL_MODELS:
        print("\n" + "=" * 60)
        logger.info("The following models require manual download:")
        print()
        for filename, info in MANUAL_MODELS.items():
            dest = Path(filename)
            if dest.exists():
                logger.info(f"  ✓ {filename} — already present")
            else:
                logger.warning(f"  ✗ {filename} — {info['description']}")
                logger.info(f"    Source: {info['source']}")
                logger.info(f"    Instructions: {info['instructions']}")
                logger.info(f"    Place at: {dest.absolute()}")
                print()

    print("=" * 60)
    logger.info("Model download complete! Run the server with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
