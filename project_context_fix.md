### 1. Current pipeline order & enabled stages
- **Stage order**: `old_photo_repair` -> `colorize` -> `denoise` -> `face_restore` -> `upscale`
- **Which stages are enabled/disabled for this test**:
  - `old_photo_repair` (BOPBTL): **Enabled**
  - `colorize` (DDColor): **Enabled**
  - `denoise` (NAFNet): **Enabled**
  - `face_restore` (GFPGAN): **Enabled** (but skips processing because no faces are detected in the Taj Mahal image).
  - `upscale` (Real-ESRGAN): **Enabled**

### 2. Per-stage config
- **old_photo_repair (BOPBTL)**:
  - max_side value: `1200`
  - HR mode (true/false): **Depends on entrypoint**. `True` in the evaluation script (`RestorationMode.ADVANCED`), but defaults to `False` (`STANDARD`) when called via the FastAPI endpoint.
  - any other flags passed to test.py: `--Scratch_and_Quality_restore`, `--gpu_ids 0` (or `-1` if fallback), and `--HR`. (Plus an automatic mid-flight retry on GPU with `max_side=768` if the 1200px run throws an Out-Of-Memory error).
- **colorize (DDColor)**:
  - detection mode (auto/forced) and current threshold logic: `mode=auto` (Detects if image is gray/sepia based on `channel_corr` > 0.95 or similar).
  - any reference-guided color transfer step: **Implemented & Enabled**. It runs Reinhard color transfer in LAB space after DDColor generates the initial color map, using `taj_mahal.jpg` as the reference.
- **denoise (NAFNet)**:
  - enabled for this run?: **Yes**.
  - position in pipeline?: Runs immediately after `colorize` and before `face_restore`.
- **face_restore**:
  - enabled/disabled: **Enabled**.
  - model: GFPGAN
- **upscale (Real-ESRGAN)**:
  - outscale factor: `4` (Advanced Mode/Eval script) or `2` (Standard Mode/FastAPI default).
  - tile size / tile padding settings: Defaults (not explicitly passed, likely 400/10).

### 3. Hardware / environment
- **GPU + VRAM**: NVIDIA GeForce RTX 3050 Laptop GPU, **6GB VRAM**.
- **CUDA version**: 13.2
- **Any recent OOM/CPU-fallback issues**: Yes. The `BOPBTL` restoration U-Net requires ~13GB VRAM when processing a `1200x896` image. It triggered an OOM crash. We have just added a fix that catches this OOM, downscales the input to a max side of `768px`, and retries on the GPU (which succeeds), rather than falling back to the 10x slower CPU route. The backend is currently idling with `0 MiB / 6144 MiB` Python VRAM usage, meaning memory is successfully freed after runs.

### 4. Known issues - current state
- **Archway shadow going flat black**: **FIXED** (post-BOPBTL quality checks blend original pixels back into large solid-black voids).
- **Edge flare artifact**: **FIXED** (post-BOPBTL quality checks detect bright variance on edges and blend original pixels back).
- **Sepia bleed-through in colorize**: **FIXED** (Image is forcefully cast to single-channel gray before hitting DDColor, eliminating the tan wash).
- **Photo border not cropped**: **FIXED** (Added `crop-to-content` preprocessing step before the pipeline starts).
- **Crack removal quality (macro-cracks)**: **STILL BROKEN**. BOPBTL running at high resolutions cannot "see" the large structural cracks due to its limited receptive field (mask/image resolution must match for test.py).
- **Foliage colorization & Muted/Hazy colors**: **STILL BROKEN**. The Reinhard color transfer using the clean reference photo forces an artificial/cinematic color grade that ruins the natural DDColor output. (We disabled this previously, but re-enabled it per your request to revert to "previous code").
- **Pathway texture artifacts (painterly/smooth blobs)**: **STILL BROKEN**. Caused by `NAFNet` aggressively destroying film grain and natural high-frequency texture. (We disabled this previously, but re-enabled it per your request).

### 5. Eval harness status
- Does app/eval/ exist and run?: **Yes**. The pipeline can be evaluated using `scripts/generate_taj_report.py`.
- Latest PSNR/SSIM/LPIPS numbers: 
  - PSNR: `14.52` dB
  - SSIM: `0.5620`
  - LPIPS: `0.5110`
- Any threshold-gating on report generation implemented yet?: Yes, logic dictates "Good" if SSIM >= 0.85, "Acceptable" if >= 0.70, and "Needs review" below 0.70.

### 6. Test image(s) being used
- Filename(s): `taj_mahal_hero_degraded.jpg`, resolution ~`1200x896`, degradation type: heavy scratches, physical tearing, severe sepia fading, and noise.
- Reference photo: `web-demo/public/samples/taj_mahal.jpg` (A clean, modern photograph of the Taj Mahal used for Reinhard color transfer).

### 7. File/module locations
- Pipeline orchestration: `f:\AI Image Restoration\backend\app\ml\pipeline.py`
- Stage implementations: `f:\AI Image Restoration\backend\app\ml\stages\`
- Colorize logic: `f:\AI Image Restoration\backend\app\ml\stages\colorize.py`
- Quality checks: `f:\AI Image Restoration\backend\app\ml\quality_checks.py`
- Eval harness: `f:\AI Image Restoration\backend\scripts\generate_taj_report.py`

### 8. Anything explicitly out of scope for this fix round
- Rewriting BOPBTL's internal architecture to upscale the mask/image independently.
- Changing hardware limitations.

### 9. What you want prioritized this round
*(Awaiting user input! From the context, the two most pressing visual issues created by our reversion are the **hazy/inconsistent colors** (Reinhard) and the **painterly/smooth textures** (NAFNet). Let me know what you want tackled first!)*
