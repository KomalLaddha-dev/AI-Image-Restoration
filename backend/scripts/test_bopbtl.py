import asyncio
import cv2
import numpy as np
from app.ml.stages.bopbtl_restore import BOPBTLStage
from loguru import logger

async def main():
    stage = BOPBTLStage()
    logger.info("Loading stage...")
    stage.load()
    
    # Create dummy image
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.putText(img, "Test", (50, 128), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    logger.info("Processing image...")
    try:
        out = await stage.process(img)
        logger.info(f"Success! Output shape: {out.shape}")
    except Exception as e:
        logger.error(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
