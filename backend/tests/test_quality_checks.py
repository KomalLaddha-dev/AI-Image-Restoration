import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import cv2
import numpy as np
from app.ml.quality_checks import check_post_bopbtl_quality

def test_detail_loss_detection():
    # Create synthetic test image with texture in shadows
    h, w = 576, 768
    pre = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Shadow region in center (mean ~50, std ~15)
    rng = np.random.default_rng(42)
    pre[200:300, 300:400] = np.clip(50 + rng.normal(0, 15, (100, 100, 3)), 0, 255).astype(np.uint8)
    
    # 1. Output where detail is preserved (similar std)
    post_good = pre.copy()
    warnings_good = check_post_bopbtl_quality(pre, post_good)
    assert len(warnings_good) == 0, f"Expected 0 warnings for good restoration, got: {warnings_good}"
    print("PASS: Clean restoration generated 0 warnings.")

    # 2. Output where shadow region is crushed to flat black void (mean ~5, std ~0)
    post_void = pre.copy()
    post_void[200:300, 300:400] = 5  # Flat black void
    warnings_void = check_post_bopbtl_quality(pre, post_void)
    assert any("possible detail loss in shadow region" in w for w in warnings_void), \
        f"Expected shadow detail loss warning, got: {warnings_void}"
    print(f"PASS: Correctly flagged shadow detail loss: {warnings_void[0]}")

    # 3. Output where left edge margin has a bright hallucinated flare (+60 shift)
    post_flare = pre.copy()
    post_flare[100:200, 0:60] = [150, 180, 240]  # Bright warm flare on left margin
    warnings_flare = check_post_bopbtl_quality(pre, post_flare)
    assert any("potential hallucinated artifact near margin" in w for w in warnings_flare), \
        f"Expected margin artifact warning, got: {warnings_flare}"
    print(f"PASS: Correctly flagged margin artifact flare: {warnings_flare[0]}")

if __name__ == "__main__":
    test_detail_loss_detection()
    print("All automated quality check tests passed successfully!")
