# Heritage Restore: Taj Mahal Restoration Quality Report

We have executed the AI Restoration pipeline on the degraded Taj Mahal archival plate and evaluated the output. To ensure the highest quality results, we enabled the backend's **Advanced Mode** which triggers the High-Resolution (HR) pipeline in the BOPBTL stage.

## Visual Quality Evaluation

1. **Deep Crack & Scratch Removal (Old Photo Repair)**
   * **Improvement**: The prominent, dark vertical crack running straight down through the center of the main dome and archway in the original 19th-century photographic plate has been **completely removed and seamlessly inpainted**.
   * Fine surface scratches, chemical spots, and paper grain visible across the sky, marble facade, and reflecting pool in the original plate are thoroughly cleared.

2. **Colorization Accuracy (DDColor)**
   * The original monochromatic sepia plate is now vividly colorized with realistic tones:
     * **Sky**: Natural gradient blue sky with soft white clouds.
     * **Water Reflection**: Clear, vibrant blue reflection in the central pool mirroring the sky and structure.
     * **Marble & Surroundings**: Warm ivory tone on the marble mausoleum and rich natural green foliage along the cypress trees lining the pathway.

3. **Detail & Sharpness (Real-ESRGAN Upscaling)**
   * Minarets, decorative inlaid archways, and structural geometric contours remain sharp and well-defined without blurriness or smudged edges.

## Restoration Preview

Here is a recording of the interactive Archival Restoration Study showing the Before (Degraded) and After (Restored) sliding comparison on the web interface:

![Taj Mahal Restoration Slider Preview](/C:/Users/laddh/.gemini/antigravity-ide/brain/a9d56f00-ca8c-4468-821e-709ea5aeaec0/evaluate_restored_taj_advanced_fixed_1790505615993.webp)

## Technical Adjustments Made
To achieve these results, I correctly mapped the `RestorationMode.ADVANCED` request to the `--HR` (High Resolution) flag in the underlying Microsoft BOPBTL subprocess within `pipeline.py`. The scratch testing script was also updated to request this advanced mode, which successfully smoothed out the deep structural cracks that were previously leaving faint traces.
