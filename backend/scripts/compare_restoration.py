import asyncio
import cv2
import numpy as np
from pathlib import Path
from loguru import logger

from app.ml.stages.old_photo_repair import OldPhotoRepairStage
from app.ml.stages.bopbtl_restore import BOPBTLStage
from app.ml.stages.upscale import UpscaleStage

async def main():
    logger.info("Starting comparison between OpenCV pipeline and BOPBTL pipeline...")
    
    # 1. Prepare input
    # Assuming there's a test image in backend/tests/ or backend/data/
    # We will just generate a dummy degraded image for demonstration if one isn't found
    test_img_path = Path("test_input.jpg")
    if not test_img_path.exists():
        logger.info("Creating a dummy test image with scratches...")
        img = np.ones((512, 512, 3), dtype=np.uint8) * 200
        # Add scratch
        cv2.line(img, (50, 50), (450, 450), (255, 255, 255), 3)
        cv2.imwrite(str(test_img_path), img)
        
    img = cv2.imread(str(test_img_path))

    # 2. Pipeline A: OpenCV + Upscale
    logger.info("--- PIPELINE A: OpenCV (Legacy) + Real-ESRGAN ---")
    opencv_stage = OldPhotoRepairStage()
    opencv_stage.load()
    
    upscale_stage = UpscaleStage()
    upscale_stage.load()
    
    out_a_1 = await opencv_stage.process(img.copy())
    out_a_2 = await upscale_stage.process(out_a_1)
    
    cv2.imwrite("output_pipeline_A.jpg", out_a_2)
    logger.info("Saved output_pipeline_A.jpg")

    # 3. Pipeline B: BOPBTL + Upscale
    logger.info("--- PIPELINE B: BOPBTL (Microsoft) + Real-ESRGAN ---")
    bopbtl_stage = BOPBTLStage()
    try:
        bopbtl_stage.load()
        out_b_1 = await bopbtl_stage.process(img.copy())
        out_b_2 = await upscale_stage.process(out_b_1)
        
        cv2.imwrite("output_pipeline_B.jpg", out_b_2)
        logger.info("Saved output_pipeline_B.jpg")
    except Exception as e:
        logger.error(f"Pipeline B failed: {e}")

    logger.info("Comparison complete.")

if __name__ == "__main__":
    asyncio.run(main())
