"""
RestorationPipeline — orchestrates the 5-stage restoration chain.

Each stage is:
  - Lazy-loaded (model weights only loaded on first use)
  - Independently toggleable via RestoreOptions
  - Timed for performance monitoring
  - Gracefully degraded (falls back to classical CV if ML model unavailable)

Pipeline order: old_photo_repair → colorize → denoise → face_restore → upscale
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from loguru import logger

from app.models.schemas import RestorationStage, RestorationMode, RestoreOptions, StageResult
from app.ml.stages.bopbtl_restore import BOPBTLStage
from app.ml.stages.denoise_deblur import DenoiseDeblurStage
from app.ml.stages.face_restore import FaceRestoreStage
from app.ml.stages.colorize import ColorizeStage
from app.ml.stages.upscale import UpscaleStage
from app.ml.quality_checks import check_post_bopbtl_quality
from app.utils.image_utils import resize_if_needed, auto_crop_border


@dataclass
class PipelineResult:
    """Output of a full restoration pipeline run."""
    original: np.ndarray
    restored: np.ndarray
    stage_results: list[StageResult] = field(default_factory=list)
    total_time_ms: int = 0
    warnings: list[str] = field(default_factory=list)


class RestorationPipeline:
    """
    Chains restoration stages in the correct order.

    Usage:
        pipeline = RestorationPipeline()
        result = await pipeline.restore(image, options)
    """

    # Canonical stage order — old_photo_repair must run before colorize
    # so that the scratch detection model receives a grayscale image.
    # old_photo_repair → colorize → denoise → face_restore → upscale
    STAGE_ORDER = [
        RestorationStage.OLD_PHOTO_REPAIR,
        RestorationStage.COLORIZE,
        RestorationStage.DENOISE,
        RestorationStage.FACE_RESTORE,
        RestorationStage.UPSCALE,
    ]

    def __init__(self):
        self._stages: dict[RestorationStage, object] = {
            RestorationStage.OLD_PHOTO_REPAIR: BOPBTLStage(),
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
        warnings: list[str] = []
        original = image.copy()
        current = image.copy()

        # Cap input size to prevent OOM on very large images
        current, scale = resize_if_needed(current, max_side=2048)
        if scale < 1.0:
            logger.info(f"Input image resized by {scale:.2f}x before pipeline")
            warnings.append(f"Input image resized to avoid OOM.")

        if getattr(options, "crop_borders", False):
            pre_crop_shape = current.shape
            current = auto_crop_border(current)
            if current.shape != pre_crop_shape:
                logger.info(f"Auto-cropped border: {pre_crop_shape[:2]} -> {current.shape[:2]}")
                warnings.append("Physical print border detected and removed.")

        # Determine enabled stages based on PRD
        enabled = {RestorationStage.OLD_PHOTO_REPAIR, RestorationStage.UPSCALE}
        if options.denoise:
            enabled.add(RestorationStage.DENOISE)
        if options.face_restore:
            enabled.add(RestorationStage.FACE_RESTORE)
        if options.colorize:
            enabled.add(RestorationStage.COLORIZE)

        stage_order_str = " → ".join(s.value for s in self.STAGE_ORDER)
        enabled_str = ", ".join(s.value for s in self.STAGE_ORDER if s in enabled)
        logger.info(f"Pipeline order: {stage_order_str}")
        logger.info(f"Enabled stages: {enabled_str}")

        for stage_key in self.STAGE_ORDER:
            if stage_key not in enabled:
                if stage_key == RestorationStage.COLORIZE:
                    logger.info("Colorization requested: false")
                    logger.info("Colorize: SKIPPED — disabled by user")
                else:
                    logger.info(f"{stage_key.value} stage: disabled by options, skipping")
                    
                stage_results.append(
                    StageResult(stage=stage_key.value, processing_time_ms=0, applied=False)
                )
                continue

            stage = self._stages[stage_key]
            stage_start = time.perf_counter()

            try:
                logger.info(f"Running stage: {stage_key.value}")
                h_in, w_in = current.shape[:2]
                
                if stage_key == RestorationStage.COLORIZE:
                    logger.info("Colorization requested: true")
                    mode = options.colorization_mode.value
                    current = await stage.process(current, colorization_mode=mode)
                    
                    if getattr(options, "reference_monument_id", None):
                        import cv2
                        from pathlib import Path
                        ref_path = Path(f"F:/AI Image Restoration/web-demo/public/samples/{options.reference_monument_id}.jpg")
                        if ref_path.exists():
                            try:
                                ref_img = cv2.imread(str(ref_path))
                                if ref_img is not None:
                                    from app.utils.color_transfer import apply_color_transfer
                                    current = apply_color_transfer(current, ref_img)
                                    logger.info(f"Applied reference-guided color transfer using {ref_path.name}")
                                    warnings.append(f"Reference-guided color transfer applied using {options.reference_monument_id}")
                            except Exception as e:
                                logger.error(f"Failed to apply color transfer: {e}")
                                warnings.append("Reference-guided color transfer failed.")
                        else:
                            logger.warning(f"Reference image not found at {ref_path}")
                    
                    # FREE VRAM: Unload colorize model immediately to ensure BOPBTL has enough memory
                    stage.unload()
                    import torch
                    torch.cuda.empty_cache()
                elif stage_key == RestorationStage.OLD_PHOTO_REPAIR:
                    pre_bopbtl = current.copy()
                    is_hr = options.mode == RestorationMode.ADVANCED
                    
                    # Run BOPBTL at 1200 max_side to preserve sharpness.
                    # It will fall back to CPU if it hits a CUDA OOM on 6GB cards.
                    current = await stage.process(current, use_hr_mode=is_hr, max_bopbtl_size=1200)
                    
                    # Automated post-BOPBTL quality checks & fix
                    from app.ml.quality_checks import check_post_bopbtl_quality, fix_post_bopbtl_artifacts
                    bopbtl_warnings = check_post_bopbtl_quality(pre_bopbtl, current)
                    if bopbtl_warnings and is_hr:
                        current = fix_post_bopbtl_artifacts(pre_bopbtl, current)
                        logger.info("Applied automatic fix for HR mode artifacts (blended original pixels)")
                    warnings.extend(bopbtl_warnings)
                elif stage_key == RestorationStage.UPSCALE:
                    outscale = 4 if options.mode == RestorationMode.ADVANCED else 2
                    current = await stage.process(current, outscale=outscale)
                else:
                    current = await stage.process(current)
                
                h_out, w_out = current.shape[:2]
                elapsed_ms = int((time.perf_counter() - stage_start) * 1000)
                stage_results.append(
                    StageResult(stage=stage_key.value, processing_time_ms=elapsed_ms)
                )
                
                # PRD Logging Requirement #9
                from app.config import get_settings
                device_str = "GPU" if get_settings().device == "cuda" else "CPU"
                logger.info(
                    f"Stage [{stage_key.value}] | Time: {elapsed_ms}ms | Device: {device_str} | "
                    f"Input: {w_in}x{h_in} | Output: {w_out}x{h_out}"
                )

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
                warnings.append(f"{stage_key.value} failed: {e}")
                
                # PRD: If BOPBTL cannot initialize, fail explicitly.
                if stage_key == RestorationStage.OLD_PHOTO_REPAIR:
                    raise RuntimeError(f"Mandatory stage BOPBTL failed: {e}") from e

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
            warnings=warnings
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
