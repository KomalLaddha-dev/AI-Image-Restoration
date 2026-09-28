"""
Quality checks for image restoration pipeline stages.
Provides objective, automated detection of regressions:
- Shadow/contrast detail loss (e.g. structure crushed into flat black voids)
- Hallucinated artifacts/flares (e.g. anomalous luminance/color shifts near margins)
"""

from __future__ import annotations
import cv2
import numpy as np
from loguru import logger


def check_post_bopbtl_quality(
    pre_bopbtl_img: np.ndarray,
    post_bopbtl_img: np.ndarray,
    shadow_lum_threshold: float = 80.0,
    min_input_std: float = 8.0,
    max_output_std_ratio: float = 0.40,
    patch_size: int = 48,
    stride: int = 24,
) -> list[str]:
    """
    Automated check on BOPBTL restoration output against its input.

    1. Detail Loss Check:
       Flags dark/shadow regions where input had texture/structure but output
       std dropped significantly (structure -> flat block of near-uniform value).

    2. Artifact Check:
       Flags regions where output has notably different mean color/brightness
       relative to input at corresponding positions, especially near edges/margins.

    Returns:
        List of warning messages generated.
    """
    warnings: list[str] = []
    h_out, w_out = post_bopbtl_img.shape[:2]

    # Align pre-BOPBTL image to post-BOPBTL dimensions for 1:1 patch spatial mapping
    if pre_bopbtl_img.shape[:2] != (h_out, w_out):
        pre_aligned = cv2.resize(pre_bopbtl_img, (w_out, h_out), interpolation=cv2.INTER_AREA)
    else:
        pre_aligned = pre_bopbtl_img

    gray_in = cv2.cvtColor(pre_aligned, cv2.COLOR_BGR2GRAY)
    gray_out = cv2.cvtColor(post_bopbtl_img, cv2.COLOR_BGR2GRAY)

    # Track warned regions to avoid spamming overlapping patch warnings
    detail_loss_count = 0
    margin_artifact_count = 0
    interior_artifact_count = 0

    for y in range(0, h_out - patch_size + 1, stride):
        for x in range(0, w_out - patch_size + 1, stride):
            p_in = gray_in[y : y + patch_size, x : x + patch_size]
            p_out = gray_out[y : y + patch_size, x : x + patch_size]

            mean_in = float(np.mean(p_in))
            std_in = float(np.std(p_in))
            mean_out = float(np.mean(p_out))
            std_out = float(np.std(p_out))

            # 1. Detail Loss in Dark/Shadow Regions
            if mean_in < shadow_lum_threshold and std_in >= min_input_std:
                # Structure crushed into flat dark void
                if std_out <= 3.5 and (std_out < std_in * max_output_std_ratio or mean_out < 20.0):
                    msg = (
                        f"BOPBTL: possible detail loss in shadow region at "
                        f"({x},{y})-({x+patch_size},{y+patch_size}), std dropped from {std_in:.1f} to {std_out:.1f}"
                    )
                    logger.warning(msg)
                    warnings.append(msg)
                    detail_loss_count += 1

            # 2. Hallucinated Artifacts / Flares
            is_margin = (
                (x < 0.15 * w_out)
                or (x + patch_size > 0.85 * w_out)
                or (y < 0.15 * h_out)
                or (y + patch_size > 0.85 * h_out)
            )

            lum_diff = abs(mean_out - mean_in)
            bgr_in = pre_aligned[y : y + patch_size, x : x + patch_size]
            bgr_out = post_bopbtl_img[y : y + patch_size, x : x + patch_size]
            color_diff = float(np.max(np.abs(np.mean(bgr_out, axis=(0, 1)) - np.mean(bgr_in, axis=(0, 1)))))

            # Near margins (edge flares, tan blotches): lower threshold
            if is_margin:
                if lum_diff >= 35.0 or color_diff >= 40.0:
                    msg = (
                        f"BOPBTL: possible spurious edge artifact near margin at "
                        f"({x},{y})-({x+patch_size},{y+patch_size}), mean luminance shifted by {lum_diff:.1f} "
                        f"(color shift {color_diff:.1f})"
                    )
                    logger.warning(msg)
                    warnings.append(msg)
                    margin_artifact_count += 1
            else:
                # In interior regions: conservative threshold to avoid false positives on scratch repair
                if lum_diff >= 55.0 or color_diff >= 60.0:
                    msg = (
                        f"BOPBTL: possible spurious interior artifact at "
                        f"({x},{y})-({x+patch_size},{y+patch_size}), mean luminance shifted by {lum_diff:.1f} "
                        f"(color shift {color_diff:.1f})"
                    )
                    logger.warning(msg)
                    warnings.append(msg)
                    interior_artifact_count += 1

    logger.info(
        f"BOPBTL automated quality check complete: {detail_loss_count} detail-loss warnings, "
        f"{margin_artifact_count} margin-artifact warnings, {interior_artifact_count} interior-artifact warnings."
    )
    return warnings

def fix_post_bopbtl_artifacts(
    pre_bopbtl_img: np.ndarray,
    post_bopbtl_img: np.ndarray,
    shadow_lum_threshold: float = 80.0,
    min_input_std: float = 8.0,
    max_output_std_ratio: float = 0.40,
    patch_size: int = 48,
    stride: int = 12,
) -> np.ndarray:
    """
    Automatically blends pre-BOPBTL image into post-BOPBTL image to fix known HR regressions:
    1. Crushed shadows (flat black voids)
    2. Hallucinated margin flares (unwarranted extreme color/luminance shifts)
    """
    h_out, w_out = post_bopbtl_img.shape[:2]
    
    if pre_bopbtl_img.shape[:2] != (h_out, w_out):
        pre_aligned = cv2.resize(pre_bopbtl_img, (w_out, h_out), interpolation=cv2.INTER_AREA)
    else:
        pre_aligned = pre_bopbtl_img
        
    gray_in = cv2.cvtColor(pre_aligned, cv2.COLOR_BGR2GRAY)
    gray_out = cv2.cvtColor(post_bopbtl_img, cv2.COLOR_BGR2GRAY)
    
    # Create a soft mask of regions to fix (0 = use post, 1 = use pre)
    fix_mask = np.zeros((h_out, w_out), dtype=np.float32)
    
    for y in range(0, h_out - patch_size + 1, stride):
        for x in range(0, w_out - patch_size + 1, stride):
            p_in = gray_in[y : y + patch_size, x : x + patch_size]
            p_out = gray_out[y : y + patch_size, x : x + patch_size]

            mean_in = float(np.mean(p_in))
            std_in = float(np.std(p_in))
            mean_out = float(np.mean(p_out))
            std_out = float(np.std(p_out))

            needs_fix = False
            
            # 1. Detail Loss in Dark/Shadow Regions
            if mean_in < shadow_lum_threshold and std_in >= min_input_std:
                if std_out <= 3.5 and (std_out < std_in * max_output_std_ratio or mean_out < 20.0):
                    needs_fix = True

            # 2. Hallucinated Artifacts / Flares
            is_margin = (
                (x < 0.15 * w_out)
                or (x + patch_size > 0.85 * w_out)
                or (y < 0.15 * h_out)
                or (y + patch_size > 0.85 * h_out)
            )

            lum_diff = abs(mean_out - mean_in)
            bgr_in = pre_aligned[y : y + patch_size, x : x + patch_size]
            bgr_out = post_bopbtl_img[y : y + patch_size, x : x + patch_size]
            color_diff = float(np.max(np.abs(np.mean(bgr_out, axis=(0, 1)) - np.mean(bgr_in, axis=(0, 1)))))

            if is_margin:
                if lum_diff >= 35.0 or color_diff >= 40.0:
                    needs_fix = True
            else:
                if lum_diff >= 55.0 or color_diff >= 60.0:
                    needs_fix = True
                    
            if needs_fix:
                # Add to mask (will be smoothed later)
                # We use a slight gradient to feather the patch
                mask_patch = np.ones((patch_size, patch_size), dtype=np.float32)
                fix_mask[y:y+patch_size, x:x+patch_size] = np.maximum(
                    fix_mask[y:y+patch_size, x:x+patch_size], 
                    mask_patch
                )
                
    # Smooth the mask to avoid harsh block boundaries
    if np.sum(fix_mask) > 0:
        fix_mask = cv2.GaussianBlur(fix_mask, (51, 51), 0)
        
    fix_mask_3d = np.expand_dims(fix_mask, axis=-1)
    
    # Blend: pre * mask + post * (1 - mask)
    fixed_img = (pre_aligned.astype(np.float32) * fix_mask_3d) + (post_bopbtl_img.astype(np.float32) * (1.0 - fix_mask_3d))
    
    return np.clip(fixed_img, 0, 255).astype(np.uint8)
