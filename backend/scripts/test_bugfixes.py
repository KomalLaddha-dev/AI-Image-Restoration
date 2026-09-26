import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import cv2
import numpy as np
from loguru import logger
from app.ml.pipeline import RestorationPipeline
from app.models.schemas import RestoreOptions, ColorizationMode, RestorationStage

async def main():
    # Create a dummy image (1536x1024) with a sepia-like solid color and noise
    # BGR format: sepia is roughly (B: 120, G: 160, R: 200)
    img = np.zeros((1536, 1024, 3), dtype=np.uint8)
    img[:, :] = (120, 160, 200)
    
    pipeline = RestorationPipeline()
    
    logger.info("=== A/B Testing BOPBTL ===")
    bopbtl = pipeline._stages[RestorationStage.OLD_PHOTO_REPAIR]
    
    logger.info("Testing BOPBTL with HR=False")
    out_no_hr = await bopbtl.process(img, use_hr_mode=False)
    
    logger.info("Testing BOPBTL with HR=True")
    out_hr = await bopbtl.process(img, use_hr_mode=True)
    
    logger.info("=== Testing Full Pipeline (checking Stage skips and Colorize sepia detection) ===")
    opts = RestoreOptions(
        denoise=True,
        face_restore=True,
        colorization_mode=ColorizationMode.AUTO
    )
    
    result = await pipeline.restore(img, opts)
    
    for stage_result in result.stage_results:
        logger.info(f"Stage Result: {stage_result.stage} - Applied: {stage_result.applied}")

if __name__ == "__main__":
    asyncio.run(main())
