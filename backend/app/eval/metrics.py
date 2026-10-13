import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import torch

# Lazy load LPIPS to avoid overhead if not used
_lpips_model = None

def get_lpips_model():
    global _lpips_model
    if _lpips_model is None:
        try:
            import lpips
            _lpips_model = lpips.LPIPS(net='alex')
            if torch.cuda.is_available():
                _lpips_model = _lpips_model.cuda()
        except ImportError:
            print("WARNING: lpips package not installed. Run `pip install lpips`.")
            return None
    return _lpips_model

def unload_lpips_model():
    global _lpips_model
    if _lpips_model is not None:
        del _lpips_model
        _lpips_model = None


def align_images(ground_truth: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    Aligns ground truth image to target (restored) image.
    Resizes ground truth to match target dimensions, then attempts
    Enhanced Correlation Coefficient (ECC) translation alignment to correct
    any subtle shift introduced by border cropping or spatial transforms.
    Falls back gracefully to the resized ground truth if ECC fails to converge.
    """
    h_tgt, w_tgt = target.shape[:2]
    if ground_truth.shape[:2] != (h_tgt, w_tgt):
        gt_aligned = cv2.resize(ground_truth, (w_tgt, h_tgt), interpolation=cv2.INTER_LANCZOS4)
    else:
        gt_aligned = ground_truth.copy()

    try:
        gt_gray = cv2.cvtColor(gt_aligned, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.005)
        _, warp_matrix = cv2.findTransformECC(
            templateImage=target_gray,
            inputImage=gt_gray,
            warpMatrix=warp_matrix,
            motionType=cv2.MOTION_TRANSLATION,
            criteria=criteria,
            inputMask=None,
            gaussFiltSize=5
        )
        aligned = cv2.warpAffine(
            gt_aligned,
            warp_matrix,
            (w_tgt, h_tgt),
            flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
            borderMode=cv2.BORDER_REFLECT
        )
        return aligned
    except Exception:
        # Fall back cleanly to resized image
        return gt_aligned


def calculate_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calculates Peak Signal-to-Noise Ratio (PSNR)."""
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return float(psnr)


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calculates Structural Similarity Index (SSIM)."""
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
    if len(img1.shape) == 3:
        return float(ssim(img1, img2, channel_axis=2, data_range=255))
    else:
        return float(ssim(img1, img2, data_range=255))


def calculate_lpips(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calculates Learned Perceptual Image Patch Similarity (LPIPS)."""
    model = get_lpips_model()
    if model is None:
        return float('nan')
        
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    t1 = torch.from_numpy(img1_rgb.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0 * 2.0 - 1.0
    t2 = torch.from_numpy(img2_rgb.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0 * 2.0 - 1.0
    
    if torch.cuda.is_available():
        t1 = t1.cuda()
        t2 = t2.cuda()
        
    with torch.no_grad():
        dist = model(t1, t2)
        
    return float(dist.item())


def calculate_crack_edge_energy_ratio(
    restored: np.ndarray,
    degraded: np.ndarray,
    scratch_mask: np.ndarray | None = None
) -> float:
    """
    Computes Sobel edge energy in the scratch/crack region:
    ratio = mean(Sobel_energy(restored)[mask]) / mean(Sobel_energy(degraded)[mask])

    A ratio < 1.0 indicates reduction in harsh scratch boundaries towards smooth,
    coherent heritage texture.
    """
    h, w = restored.shape[:2]
    if degraded.shape[:2] != (h, w):
        degraded = cv2.resize(degraded, (w, h))

    # Convert to grayscale
    gray_res = cv2.cvtColor(restored, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_deg = cv2.cvtColor(degraded, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Compute Sobel edge energy magnitude
    gx_res = cv2.Sobel(gray_res, cv2.CV_32F, 1, 0, ksize=3)
    gy_res = cv2.Sobel(gray_res, cv2.CV_32F, 0, 1, ksize=3)
    energy_res = np.sqrt(gx_res ** 2 + gy_res ** 2)

    gx_deg = cv2.Sobel(gray_deg, cv2.CV_32F, 1, 0, ksize=3)
    gy_deg = cv2.Sobel(gray_deg, cv2.CV_32F, 0, 1, ksize=3)
    energy_deg = np.sqrt(gx_deg ** 2 + gy_deg ** 2)

    if scratch_mask is not None:
        if scratch_mask.shape[:2] != (h, w):
            scratch_mask = cv2.resize(scratch_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask_binary = scratch_mask > 0
    else:
        # Fallback: estimate high-contrast scratch mask from difference
        diff = np.abs(gray_deg - gray_res)
        _, mask_binary = cv2.threshold(diff.astype(np.uint8), 30, 255, cv2.THRESH_BINARY)
        mask_binary = mask_binary > 0

    if np.sum(mask_binary) == 0:
        return 1.0

    mean_res = float(np.mean(energy_res[mask_binary]))
    mean_deg = float(np.mean(energy_deg[mask_binary]))

    if mean_deg == 0:
        return 1.0

    return float(mean_res / mean_deg)


def evaluate_image_quality(
    ground_truth_path: str,
    restored_path: str,
    degraded_path: str | None = None,
    scratch_mask_path: str | None = None,
) -> dict[str, float]:
    """
    Calculates comprehensive image quality metrics:
    - Luminance PSNR / SSIM (Y channel in YCrCb)
    - Colour PSNR / SSIM (3-channel BGR)
    - LPIPS perceptual distance
    - Crack-region edge-energy ratio (if degraded image provided)
    """
    gt_img = cv2.imread(ground_truth_path)
    restored_img = cv2.imread(restored_path)
    
    if gt_img is None:
        raise ValueError(f"Could not read ground truth image: {ground_truth_path}")
    if restored_img is None:
        raise ValueError(f"Could not read restored image: {restored_path}")

    # Align ground truth to restored output
    aligned_gt = align_images(gt_img, restored_img)

    # 1. Luminance PSNR & SSIM (Y channel)
    gt_ycrcb = cv2.cvtColor(aligned_gt, cv2.COLOR_BGR2YCrCb)
    res_ycrcb = cv2.cvtColor(restored_img, cv2.COLOR_BGR2YCrCb)
    gt_y = gt_ycrcb[:, :, 0]
    res_y = res_ycrcb[:, :, 0]

    luma_psnr = calculate_psnr(gt_y, res_y)
    luma_ssim = calculate_ssim(gt_y, res_y)

    # 2. Colour PSNR & SSIM (BGR multichannel)
    color_psnr = calculate_psnr(aligned_gt, restored_img)
    color_ssim = calculate_ssim(aligned_gt, restored_img)

    # 3. LPIPS
    lpips_val = calculate_lpips(aligned_gt, restored_img)

    # 4. Crack region edge energy ratio
    crack_ratio = 1.0
    if degraded_path:
        deg_img = cv2.imread(degraded_path)
        if deg_img is not None:
            mask = cv2.imread(scratch_mask_path, cv2.IMREAD_GRAYSCALE) if scratch_mask_path else None
            crack_ratio = calculate_crack_edge_energy_ratio(restored_img, deg_img, mask)

    return {
        'luma_psnr': luma_psnr,
        'luma_ssim': luma_ssim,
        'color_psnr': color_psnr,
        'color_ssim': color_ssim,
        'lpips': lpips_val,
        'crack_ratio': crack_ratio,
        # Backward compatibility aliases
        'psnr': color_psnr,
        'ssim': color_ssim,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate quality metrics between ground truth and restored.")
    parser.add_argument("gt", help="Path to ground truth image")
    parser.add_argument("restored", help="Path to restored image")
    parser.add_argument("--degraded", default=None, help="Path to degraded image")
    parser.add_argument("--mask", default=None, help="Path to scratch mask")
    args = parser.parse_args()
    
    metrics = evaluate_image_quality(args.gt, args.restored, args.degraded, args.mask)
    print(f"Luma PSNR:     {metrics['luma_psnr']:.2f} dB")
    print(f"Luma SSIM:     {metrics['luma_ssim']:.4f}")
    print(f"Color PSNR:    {metrics['color_psnr']:.2f} dB")
    print(f"Color SSIM:    {metrics['color_ssim']:.4f}")
    print(f"LPIPS:         {metrics['lpips']:.4f}")
    print(f"Crack Ratio:   {metrics['crack_ratio']:.4f}")
