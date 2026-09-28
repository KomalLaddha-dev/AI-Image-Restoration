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
            # Use GPU if available
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

def calculate_psnr(img1, img2):
    """Calculates Peak Signal-to-Noise Ratio (PSNR)."""
    # Ensure images have same shape
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

def calculate_ssim(img1, img2):
    """Calculates Structural Similarity Index (SSIM)."""
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
    # Convert to grayscale for SSIM if needed, or use multichannel
    if len(img1.shape) == 3:
        # channel_axis is the last axis for OpenCV (H, W, C)
        return ssim(img1, img2, channel_axis=2, data_range=255)
    else:
        return ssim(img1, img2, data_range=255)

def calculate_lpips(img1, img2):
    """Calculates Learned Perceptual Image Patch Similarity (LPIPS)."""
    model = get_lpips_model()
    if model is None:
        return float('nan')
        
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Convert BGR (OpenCV) to RGB
    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    # Convert to tensor and normalize to [-1, 1] for LPIPS
    # LPIPS expects NCHW format
    t1 = torch.from_numpy(img1_rgb.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0 * 2.0 - 1.0
    t2 = torch.from_numpy(img2_rgb.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0 * 2.0 - 1.0
    
    if torch.cuda.is_available():
        t1 = t1.cuda()
        t2 = t2.cuda()
        
    with torch.no_grad():
        dist = model(t1, t2)
        
    return dist.item()

def evaluate_image_quality(ground_truth_path, restored_path):
    """Calculates PSNR, SSIM, and LPIPS between two images."""
    gt_img = cv2.imread(ground_truth_path)
    restored_img = cv2.imread(restored_path)
    
    if gt_img is None:
        raise ValueError(f"Could not read ground truth image: {ground_truth_path}")
    if restored_img is None:
        raise ValueError(f"Could not read restored image: {restored_path}")
        
    results = {
        'psnr': calculate_psnr(gt_img, restored_img),
        'ssim': calculate_ssim(gt_img, restored_img),
        'lpips': calculate_lpips(gt_img, restored_img)
    }
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate quality metrics between two images.")
    parser.add_argument("gt", help="Path to ground truth image")
    parser.add_argument("restored", help="Path to restored image")
    args = parser.parse_args()
    
    metrics = evaluate_image_quality(args.gt, args.restored)
    print(f"PSNR:  {metrics['psnr']:.2f}")
    print(f"SSIM:  {metrics['ssim']:.4f}")
    print(f"LPIPS: {metrics['lpips']:.4f}")
