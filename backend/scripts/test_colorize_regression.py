import asyncio
import numpy as np
from loguru import logger
import sys, os
sys.path.insert(0, ".")

from app.ml.pipeline import RestorationPipeline
from app.models.schemas import RestoreOptions, ColorizationMode

async def test_colorize_regression():
    pipeline = RestorationPipeline()
    # Create a dummy image
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)

    logger.info("=== Test A: colorize=false ===")
    opts_a = RestoreOptions(colorize=False, colorization_mode=ColorizationMode.AUTO)
    res_a = await pipeline.restore(dummy_img, opts_a)
    assert not any(s.stage == "colorize" and s.applied for s in res_a.stage_results), "Test A failed"
    logger.info("Test A passed")

    logger.info("=== Test B: colorize=true, mode=force ===")
    opts_b = RestoreOptions(colorize=True, colorization_mode=ColorizationMode.FORCE)
    res_b = await pipeline.restore(dummy_img, opts_b)
    assert any(s.stage == "colorize" and s.applied for s in res_b.stage_results), "Test B failed"
    logger.info("Test B passed")

    logger.info("=== Test C: colorize=true, mode=auto ===")
    opts_c = RestoreOptions(colorize=True, colorization_mode=ColorizationMode.AUTO)
    # Since dummy_img is all zeros, it's grayscale, so auto should apply colorization
    res_c = await pipeline.restore(dummy_img, opts_c)
    assert any(s.stage == "colorize" and s.applied for s in res_c.stage_results), "Test C failed"
    logger.info("Test C passed")

if __name__ == "__main__":
    asyncio.run(test_colorize_regression())
