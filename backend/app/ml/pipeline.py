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
    ai_reconstructed: bool = False


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
    # Canonical stage order
    STAGE_ORDER = [
        RestorationStage.CRACK_INPAINT,
        RestorationStage.OLD_PHOTO_REPAIR,
        RestorationStage.COLORIZE,
        RestorationStage.DENOISE,
        RestorationStage.FACE_RESTORE,
        RestorationStage.UPSCALE,
    ]

    def __init__(self):
        from app.ml.stages.crack_inpaint import CrackInpaintStage
        from app.ml.stages.generative_enhance import GenerativeEnhancer
        self.generative_enhancer = GenerativeEnhancer()
        self._stages: dict[RestorationStage, object] = {
            RestorationStage.CRACK_INPAINT: CrackInpaintStage(),
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
        if options is None:
            options = RestoreOptions()

        pipeline_start = time.perf_counter()
        stage_results: list[StageResult] = []
        warnings: list[str] = []
        original = image.copy()
        current = image.copy()

        max_side = getattr(options, "max_side", 768) or 768
        current, scale = resize_if_needed(current, max_side=max_side)
        if scale < 1.0:
            logger.info(f"Input image resized to max_side={max_side} by {scale:.2f}x before pipeline")
            warnings.append(f"Input image resized to max_side={max_side} to avoid OOM.")

        if getattr(options, "crop_borders", False):
            pre_crop_shape = current.shape
            current = auto_crop_border(current)
            if current.shape != pre_crop_shape:
                logger.info(f"Auto-cropped border: {pre_crop_shape[:2]} -> {current.shape[:2]}")
                warnings.append("Physical print border detected and removed.")

        enabled = {RestorationStage.OLD_PHOTO_REPAIR, RestorationStage.UPSCALE}
        if getattr(options, "crack_inpaint", True):
            enabled.add(RestorationStage.CRACK_INPAINT)
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
                
                if stage_key == RestorationStage.CRACK_INPAINT:
                    current = await stage.process(current)
                elif stage_key == RestorationStage.COLORIZE:
                    logger.info("Colorization requested: true")
                    mode = options.colorization_mode.value
                    current = await stage.process(current, colorization_mode=mode)
                    
                    # Reinhard color transfer is OFF by default; never apply when reference is ground truth
                    if (
                        getattr(options, "reference_guided_color", False)
                        and getattr(options, "reference_monument_id", None)
                        and not getattr(options, "is_eval_ground_truth", False)
                    ):
                        import cv2
                        from pathlib import Path
                        # Default reference image logic: Try from backend static/samples or fallback
                        ref_path = Path("static/samples") / f"{options.reference_monument_id}.jpg"
                        if not ref_path.exists():
                            # Fallback if someone runs it from another root
                            ref_path = Path(__file__).parent.parent.parent.parent / "web-demo/public/samples" / f"{options.reference_monument_id}.jpg"
                        if ref_path.exists():
                            try:
                                ref_img = cv2.imread(str(ref_path))
                                if ref_img is not None:
                                    from app.utils.color_transfer import apply_color_transfer
                                    blend_str = getattr(options, "reference_blend_strength", 0.3)
                                    current = apply_color_transfer(current, ref_img, strength=blend_str)
                                    logger.info(f"Applied reference-guided color transfer using {ref_path.name} with strength {blend_str}")
                                    warnings.append(f"Reference-guided color transfer applied using {options.reference_monument_id}")
                            except Exception as e:
                                logger.error(f"Failed to apply color transfer: {e}")
                                warnings.append("Reference-guided color transfer failed.")
                        else:
                            logger.warning(f"Reference image not found at {ref_path}")
                    
                    stage.unload()
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                elif stage_key == RestorationStage.OLD_PHOTO_REPAIR:
                    pre_bopbtl = current.copy()
                    
                    # HR mode is always False, max_side=768 by default
                    is_hr = False
                    current = await stage.process(current, use_hr_mode=is_hr, max_bopbtl_size=max_side)
                    
                    from app.ml.quality_checks import check_post_bopbtl_quality, fix_post_bopbtl_artifacts
                    bopbtl_warnings = check_post_bopbtl_quality(pre_bopbtl, current)
                    if bopbtl_warnings and is_hr:
                        current = fix_post_bopbtl_artifacts(pre_bopbtl, current)
                        logger.info("Applied automatic fix for HR mode artifacts")
                    warnings.extend(bopbtl_warnings)
                elif stage_key == RestorationStage.DENOISE:
                    denoise_strength = getattr(options, "denoise_strength", 0.0)
                    current = await stage.process(current, denoise_strength=denoise_strength)
                elif stage_key == RestorationStage.UPSCALE:
                    outscale = 4 if options.mode in (RestorationMode.ADVANCED, RestorationMode.ENHANCED) else 2
                    
                    if options.mode == RestorationMode.ENHANCED:
                        import asyncio
                        provider_type = getattr(options, "generative_provider", "off").value if hasattr(getattr(options, "generative_provider", None), "value") else getattr(options, "generative_provider", "off")
                        self.generative_enhancer.load(provider_type)
                        enhanced, success = await asyncio.to_thread(self.generative_enhancer.process, current)
                        self.generative_enhancer.unload()
                        
                        if success:
                            current = enhanced
                            warnings.append("AI reconstruction applied via generative model.")
                            # We can set ai_reconstructed in the outer result, but the pipeline doesn't have an ai_reconstructed field in PipelineResult yet. Let's add it.
                        else:
                            current = await stage.process(current, outscale=outscale)
                    else:
                        current = await stage.process(current, outscale=outscale)
                else:
                    current = await stage.process(current)
                
                h_out, w_out = current.shape[:2]
                elapsed_ms = int((time.perf_counter() - stage_start) * 1000)
                stage_results.append(
                    StageResult(stage=stage_key.value, processing_time_ms=elapsed_ms)
                )
                
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
            warnings=warnings,
            ai_reconstructed=any("AI reconstruction applied" in w for w in warnings)
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
