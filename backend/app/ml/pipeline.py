"""
RestorationPipeline — orchestrates the 5-stage restoration chain.

Each stage is:
  - Lazy-loaded (model weights only loaded on first use)
  - Independently toggleable via RestoreOptions
  - Timed for performance monitoring
  - Gracefully degraded (falls back to classical CV if ML model unavailable)

Pipeline order: old_photo_repair → denoise → face_restore → colorize → upscale
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from loguru import logger

from app.models.schemas import RestorationStage, RestoreOptions, StageResult
from app.ml.stages.old_photo_repair import OldPhotoRepairStage
from app.ml.stages.denoise_deblur import DenoiseDeblurStage
from app.ml.stages.face_restore import FaceRestoreStage
from app.ml.stages.colorize import ColorizeStage
from app.ml.stages.upscale import UpscaleStage
from app.utils.image_utils import resize_if_needed


@dataclass
class PipelineResult:
    """Output of a full restoration pipeline run."""
    original: np.ndarray
    restored: np.ndarray
    stage_results: list[StageResult] = field(default_factory=list)
    total_time_ms: int = 0


class RestorationPipeline:
    """
    Chains restoration stages in the correct order.

    Usage:
        pipeline = RestorationPipeline()
        result = await pipeline.restore(image, options)
    """

    # Canonical stage order — matches PRD Section 6.1
    STAGE_ORDER = [
        RestorationStage.OLD_PHOTO_REPAIR,
        RestorationStage.DENOISE,
        RestorationStage.FACE_RESTORE,
        RestorationStage.COLORIZE,
        RestorationStage.UPSCALE,
    ]

    def __init__(self):
        self._stages: dict[RestorationStage, object] = {
            RestorationStage.OLD_PHOTO_REPAIR: OldPhotoRepairStage(),
            RestorationStage.DENOISE: DenoiseDeblurStage(),
            RestorationStage.FACE_RESTORE: FaceRestoreStage(),
            RestorationStage.COLORIZE: ColorizeStage(),
            RestorationStage.UPSCALE: UpscaleStage(),
        }
        logger.info(
            f"RestorationPipeline initialized with {len(self._stages)} stages"
        )

    async def restore(
        self,
        image: np.ndarray,
        options: RestoreOptions | None = None,
    ) -> PipelineResult:
        """
        Run the restoration pipeline on an input image.

        Args:
            image: BGR NumPy array (OpenCV format).
            options: Which stages to enable and quality mode.

        Returns:
            PipelineResult with original, restored image, and per-stage timing.
        """
        if options is None:
            options = RestoreOptions()

        pipeline_start = time.perf_counter()
        stage_results: list[StageResult] = []
        original = image.copy()
        current = image.copy()

        # Cap input size to prevent OOM on very large images
        current, scale = resize_if_needed(current, max_side=2048)
        if scale < 1.0:
            logger.info(f"Input image resized by {scale:.2f}x before pipeline")

        # Execute stages in canonical order, only if enabled
        enabled = set(options.stages)

        for stage_key in self.STAGE_ORDER:
            if stage_key not in enabled:
                stage_results.append(
                    StageResult(stage=stage_key.value, processing_time_ms=0, applied=False)
                )
                continue

            stage = self._stages[stage_key]
            stage_start = time.perf_counter()

            try:
                logger.info(f"Running stage: {stage_key.value}")
                current = await stage.process(current)
                elapsed_ms = int((time.perf_counter() - stage_start) * 1000)
                stage_results.append(
                    StageResult(stage=stage_key.value, processing_time_ms=elapsed_ms)
                )
                logger.info(f"Stage {stage_key.value} completed in {elapsed_ms}ms")

            except Exception as e:
                elapsed_ms = int((time.perf_counter() - stage_start) * 1000)
                logger.error(f"Stage {stage_key.value} failed after {elapsed_ms}ms: {e}")
                stage_results.append(
                    StageResult(
                        stage=stage_key.value,
                        processing_time_ms=elapsed_ms,
                        applied=False,
                    )
                )
                # Continue pipeline — don't let one stage failure stop everything

        total_ms = int((time.perf_counter() - pipeline_start) * 1000)

        logger.info(
            f"Pipeline complete: {sum(1 for s in stage_results if s.applied)}/{len(stage_results)} "
            f"stages applied in {total_ms}ms"
        )

        return PipelineResult(
            original=original,
            restored=current,
            stage_results=stage_results,
            total_time_ms=total_ms,
        )

    def get_loaded_models(self) -> list[str]:
        """Return names of currently loaded models (for health check)."""
        loaded = []
        for key, stage in self._stages.items():
            if hasattr(stage, "is_available") and stage.is_available():
                loaded.append(key.value)
        return loaded

    def preload(self, stages: list[RestorationStage] | None = None) -> None:
        """
        Eagerly load model weights for specified stages.
        Call during app startup to avoid cold-start latency on first request.
        """
        targets = stages or list(self._stages.keys())
        for key in targets:
            stage = self._stages.get(key)
            if stage and hasattr(stage, "load"):
                try:
                    stage.load()
                except Exception as e:
                    logger.error(f"Failed to preload {key.value}: {e}")

    def unload_all(self) -> None:
        """Free all model memory. Call on shutdown."""
        for key, stage in self._stages.items():
            if hasattr(stage, "unload"):
                try:
                    stage.unload()
                except Exception as e:
                    logger.error(f"Failed to unload {key.value}: {e}")
