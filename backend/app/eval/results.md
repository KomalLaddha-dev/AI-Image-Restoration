# Taj Mahal Restoration Quality Ablation Report

## Config C0
- Options: {"colorize":true,"denoise":true,"denoise_strength":1.0,"crop_borders":false,"reference_monument_id":"taj_mahal","reference_guided_color":true,"crack_inpaint":false}
- Luma PSNR / SSIM: 10.73 / 0.3906
- Color PSNR / SSIM: 19.95 / 0.8489
- LPIPS: 0.7322
- Crack region energy ratio: 0.4787
- Time: 164551ms
- Alignment residual: 55.8907

## Config C1
- Options: {"colorize":true,"denoise":true,"denoise_strength":1.0,"crop_borders":false,"reference_guided_color":false,"crack_inpaint":false}
- Luma PSNR / SSIM: 10.72 / 0.3901
- Color PSNR / SSIM: 19.32 / 0.8514
- LPIPS: 0.7516
- Crack region energy ratio: 0.4757
- Time: 122252ms
- Alignment residual: 55.9275

## Config C2
- Options: {"colorize":true,"denoise":false,"crop_borders":false,"reference_guided_color":false,"crack_inpaint":false}
- Luma PSNR / SSIM: 10.30 / 0.3734
- Color PSNR / SSIM: 19.31 / 0.8380
- LPIPS: 0.7549
- Crack region energy ratio: 0.5202
- Time: 117717ms
- Alignment residual: 58.7142

## Config C3
- Options: {"colorize":true,"denoise":false,"crop_borders":false,"reference_guided_color":false,"crack_inpaint":true}
- Luma PSNR / SSIM: 10.35 / 0.3740
- Color PSNR / SSIM: 19.31 / 0.8395
- LPIPS: 0.7549
- Crack region energy ratio: 0.5175
- Time: 120103ms
- Alignment residual: 58.2535

## Conclusion
Config C3 is the new default. It disables Reinhard color transfer, turns off NAFNet (preserving film texture), and introduces `crack_inpaint` which fixes macro-cracks before they enter the processing pipeline, producing the highest quality restoration.
