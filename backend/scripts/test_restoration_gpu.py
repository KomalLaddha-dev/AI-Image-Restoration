import asyncio
import cv2
import sys
from pathlib import Path
from loguru import logger
import numpy as np

# Add backend directory to sys.path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.ml.pipeline import RestorationPipeline
from app.models.schemas import RestoreOptions

async def main():
    # Setup test image
    test_img_path = Path(__file__).parent.parent / "tests" / "test_data" / "scratched_photo.jpg"
    
    # If a specific test image doesn't exist, create a dummy noisy one
    if not test_img_path.exists():
        test_img_path.parent.mkdir(parents=True, exist_ok=True)
        img = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)
        cv2.imwrite(str(test_img_path), img)
        logger.info(f"Created dummy test image at {test_img_path}")
    
    img = cv2.imread(str(test_img_path))
    if img is None:
        logger.error(f"Failed to read {test_img_path}")
        return
        
    logger.info(f"Loaded test image: {img.shape}")
    
    pipeline = RestorationPipeline()
    
    options = RestoreOptions(
        denoise=False,
        face_restore=False,
        colorize=False
    )
    
    logger.info("Starting restoration pipeline (BOPBTL -> Real-ESRGAN) ...")
    
    try:
        result = await pipeline.restore(img, options)
        logger.info(f"Pipeline complete in {result.total_time_ms}ms")
        for sr in result.stage_results:
            logger.info(f"  Stage {sr.stage}: {sr.processing_time_ms}ms (Applied: {sr.applied})")
            
        out_path = Path(__file__).parent.parent / "tests" / "test_data" / "restored_gpu_test.png"
        cv2.imwrite(str(out_path), result.restored)
        logger.info(f"Saved output to {out_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
