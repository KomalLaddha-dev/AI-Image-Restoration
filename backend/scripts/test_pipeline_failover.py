import asyncio
import cv2
from pathlib import Path
from loguru import logger
import os
from dotenv import load_dotenv
load_dotenv()

from app.ml.pipeline import RestorationPipeline
from app.models.schemas import RestoreOptions, RestorationMode, GenerativeProvider

async def main():
    logger.info("Initializing pipeline...")
    pipeline = RestorationPipeline()
    
    test_img_path = r"F:\AI Image Restoration\backend\data\eval\degraded\taj_mahal_original.jpg"
    test_img = cv2.imread(test_img_path)
    if test_img is None:
        logger.error(f"Could not load image at {test_img_path}")
        return
        
    logger.info("Testing with valid Colab URL (should use HYPIR)")
    options = RestoreOptions(mode=RestorationMode.ENHANCED, target_longest_side=1200, generative_provider=GenerativeProvider.COLAB)
    result = await pipeline.restore(test_img, options)
    
    cv2.imwrite("test_outputs/failover_taj_mahal_generative.jpg", result.restored)
    
    has_generative = result.ai_reconstructed
    if has_generative:
        logger.info("HYPIR generative enhance succeeded!")
    else:
        logger.error("HYPIR generative enhance failed!")
        
    logger.info("Testing fallback by breaking the URL...")
    # Break the URL
    os.environ["COLAB_HYPIR_URL"] = "http://localhost:9999"
    result_fallback = await pipeline.restore(test_img, options)
    
    cv2.imwrite("test_outputs/failover_taj_mahal_fallback.jpg", result_fallback.restored)
    
    has_generative_fallback = result_fallback.ai_reconstructed
    if not has_generative_fallback:
        logger.info("Fallback succeeded! Generative enhancer failed cleanly, pipeline continued.")
    else:
        logger.error("Wait, generative enhance succeeded with a broken URL?")

if __name__ == "__main__":
    asyncio.run(main())
