import asyncio
import sys
from pathlib import Path
import cv2
import numpy as np

# Add the backend root to the python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.ml.stages.colorize import ColorizeStage

def generate_test_images():
    """Generate a grayscale image and a sepia image for testing."""
    # Create a base grayscale image (a simple gradient pattern)
    gray = np.zeros((512, 512, 3), dtype=np.uint8)
    for i in range(512):
        gray[:, i, :] = i // 2

    # Create a sepia image
    sepia = np.zeros((512, 512, 3), dtype=np.float64)
    normalized = gray.astype(np.float64) / 255.0
    sepia[:, :, 0] = normalized[:, :, 0] * 153  # B
    sepia[:, :, 1] = normalized[:, :, 1] * 204  # G
    sepia[:, :, 2] = normalized[:, :, 2] * 255  # R
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)

    return gray, sepia

async def main():
    print("Initializing ColorizeStage...")
    stage = ColorizeStage()
    
    gray, sepia = generate_test_images()
    
    out_dir = backend_dir / "test_outputs"
    out_dir.mkdir(exist_ok=True)
    
    cv2.imwrite(str(out_dir / "input_grayscale.jpg"), gray)
    cv2.imwrite(str(out_dir / "input_sepia.jpg"), sepia)
    
    print("\nProcessing Grayscale Image (auto mode)...")
    out_gray = await stage.process(gray, colorization_mode="auto")
    cv2.imwrite(str(out_dir / "output_grayscale.jpg"), out_gray)
    
    print("\nProcessing Sepia Image (auto mode)...")
    out_sepia = await stage.process(sepia, colorization_mode="auto")
    cv2.imwrite(str(out_dir / "output_sepia.jpg"), out_sepia)
    
    print("\nProcessing Sepia Image (force mode)...")
    out_sepia_force = await stage.process(sepia, colorization_mode="force")
    cv2.imwrite(str(out_dir / "output_sepia_force.jpg"), out_sepia_force)
    
    print("\nDone. Outputs saved to test_outputs directory.")

if __name__ == "__main__":
    asyncio.run(main())
