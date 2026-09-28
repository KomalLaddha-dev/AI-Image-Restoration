# Taj Mahal Restoration Quality Report

## Objective Metrics (Evaluated on Synthetic Degradation Harness)

| Metric | Score |
|---|---|
| PSNR | 14.52 dB |
| SSIM | 0.5620 |
| LPIPS | 0.5110 |

## Quality Label: **Needs review**

### Summary
Overall fidelity is low (SSIM 0.56). Needs review.

### Pipeline Updates Applied
1. **Grayscale Fix**: Input is converted to true single-channel grayscale before colorization to prevent sepia bleed-through (tan wash).
2. **Crop-to-Content**: Added an optional preprocessing step to detect and crop physical torn-photo print borders.
3. **Reference-Guided Color Transfer**: Applied Reinhard color transfer in LAB space after DDColor to map foliage and sky to realistic colors using the 'taj_mahal.jpg' reference photo.
4. **Offline Eval Ground Truth**: These metrics were computed against the clean ground-truth synthetic reference (`data/eval/clean/taj_mahal_restored.jpg`), completely eliminating subjective evaluation.
