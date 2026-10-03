import sys
import os
import cv2
import asyncio
from dotenv import load_dotenv

# Load env before importing our stuff so COLAB_HYPIR_URL is set
load_dotenv()

from app.ml.stages.generative_enhance import RemoteColabHYPIR

def main():
    img_path = r"F:\AI Image Restoration\backend\test_outputs\taj_mahal_final_restored.jpg"
    print(f"Loading image from {img_path}")
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to load image!")
        sys.exit(1)
        
    print(f"Original image shape: {img.shape}")
    
    # Downscale if too large to prevent Colab OOM or 20 min processing time
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim > 768:
        scale = 768 / max_dim
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        print(f"Downscaled to: {img.shape}")
    
    hypir = RemoteColabHYPIR()
    print(f"Checking Colab HYPIR health at {hypir.url}...")
    if not hypir.check_health():
        print("Colab HYPIR health check failed. Make sure the Colab server is running and the URL is correct.")
        sys.exit(1)
        
    print("Health check passed! Enhancing...")
    enhanced = hypir.enhance(img)
    
    if enhanced is None:
        print("Enhancement failed.")
        sys.exit(1)
        
    out_path = r"F:\AI Image Restoration\backend\test_outputs\taj_mahal_hypir_only.jpg"
    cv2.imwrite(out_path, enhanced)
    print(f"Enhancement complete! Saved to {out_path}")

if __name__ == "__main__":
    main()
