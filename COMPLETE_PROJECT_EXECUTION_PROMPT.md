# 🏛️ MASTER EXECUTION PROMPT: COMPLETE IMPLEMENTATION OF HERITAGE RESTORE

> **Target Project:** Heritage Restore (`f:\AI Image Restoration`)  
> **Objective:** Execute and complete all remaining phases of the project — spanning the **Monument Identification Engine ("The Left Part")**, **RAG Knowledge Base ("The Right Part")**, **Image Restoration Pipeline Hardening**, **Cinematic Web Demo**, and **Automated Benchmark Harness**.

---

## 🎯 GLOBAL RULES (STRICT CONSTRAINTS)

1. **One Phase Per Session**: Work strictly ONE phase per session. After each phase: create a conventional git commit, then **STOP and report**. Do not start the next phase until instructed.
2. **Real Verification Only**: "Verified" strictly means running the command and pasting the actual stdout/stderr output. Never fabricate, estimate, or claim a metric, test pass, or fix without measured output. If a target is missed, report the real measured number and state that it was missed.
3. **No Hallucinated Citations/URLs**: Never write citations, URLs, or source names from memory. Anything added to the corpus must originate from a network page actually fetched during execution.
4. **Scope Exclusions**: Mobile App (React Native/Expo) is completely out of scope. Focus 100% on the Web Application and FastAPI backend.

---

## 📋 STEP-BY-STEP IMPLEMENTATION ROADMAP

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COMPLETION ROADMAP                              │
│                                                                        │
│  Phase 1: CLIP Foundation Monument Identification ("The Left Part")     │
│  Phase 2: Verified RAG Corpus & Grounded Provenance ("The Right Part") │
│  Phase 3: Restoration Pipeline Overhaul & Quality Fixes                │
│  Phase 4: API & Hybrid Storage Hardening (Local + Cloudinary)          │
│  Phase 5: Cinematic Web Frontend & Mobile-First PWA Polish             │
│  Phase 6: Measured Evaluation Harness & Final Reporting                │
└────────────────────────────────────────────────────────────────────────┘
```

---

### PHASE 1: CLIP FOUNDATION MONUMENT IDENTIFICATION ("THE LEFT PART")

* **Primary Engine**: Use **CLIP (`clip-ViT-B-32`) + reference gallery**. Do NOT create or ship an ONNX classifier trained on nothing. Only add an ONNX tier if trained on real monument images with reported held-out test accuracy.
* **Scoring & Calibration**:
  * Extract visual embeddings for query and gallery items.
  * Convert cosine similarity to scores via softmax with temperature ($\tau$) across gallery classes.
  * Choose the recognition threshold from an independent held-out set that includes:
    (a) In-gallery monuments ($\ge 5$ photos per monument, including degraded and sepia ones).
    (b) Monuments NOT in the gallery.
    (c) Non-monument images (urban streets, vehicles, people, indoor spaces).
  * Report the precision/recall tradeoff and confusion matrix at the chosen threshold.
* **Separation of Gallery & Test Data**:
  * Gallery reference images must **never** be used as test images.
  * Maintain a dedicated, held-out test set with $\ge 5$ photos per monument.
* **Shared Threshold Constant**:
  * Use **one single confidence threshold constant** shared between backend and frontend (synchronized via config/API or identical constant).

---

### PHASE 2: VERIFIED RAG CORPUS & GROUNDED PROVENANCE ("THE RIGHT PART")

* **Real Page Fetching**:
  * For every text chunk in `backend/data/corpus/*.json`: fetch the actual source page (Wikipedia, Archaeological Survey of India, UNESCO, or official sites) via HTTP.
  * Paraphrase concisely, set `source_url` to the exact fetched URL, and set `"verified": true` ONLY if fetched.
  * Mark any unfetched content `"verified": false` and strictly exclude it from RAG generation context.
* **Attribution**:
  * Wikipedia-derived text must include attribution (`CC BY-SA`) in the source field.
* **Quality Audit**:
  * Spot-check 10 random chunks against their URLs and report verification results with actual responses.
* **Vector Index**:
  * Rebuild FAISS index (`all-MiniLM-L6-v2`) exclusively over `"verified": true` chunks.
  * Fall back cleanly to verified structured JSON facts if Groq API key is absent.

---

### PHASE 3: RESTORATION PIPELINE OVERHAUL & QUALITY FIXES

* **Resolution & Memory Defaults**:
  * Set `HR = False` in every entrypoint (API routes and evaluation scripts).
  * Default `max_side = 768`.
  * Keep the GPU OOM downscale-retry logic as a safety net only.
* **Colorization**:
  * Reinhard color transfer **OFF by default** (optional: a/b channels only with strength 0.3, never when the reference is the ground truth).
  * Use DDColor native LAB colorization to avoid sepia bleed.
* **Denoising & Texture Preservation**:
  * NAFNet **OFF by default**.
  * Add configurable `denoise_strength \in [0, 1]` with default `0.0`:
    $$\text{out} = s \cdot \text{denoised} + (1 - s) \cdot \text{input}$$
* **Crack & Inpainting Stage**:
  * Add new `crack_inpaint` stage before `old_photo_repair`:
    - BOPBTL scratch-mask at $\le 768$px.
    - Upsample + dilate by 3–7px.
    - Inpaint with LaMa (`cv2.inpaint` fallback).
    - Skip inpainting if mask coverage $> 15\%$.
* **Evaluation Alignment**:
  * Align ground truth to restored output before scoring.
  * Report luminance AND colour PSNR/SSIM, LPIPS, and crack-region edge-energy ratio.
  * Run across all synthetic evaluation pairs, not just Taj Mahal.

---

### PHASE 4: API & STORAGE RESILIENCE

* **Storage Failover**:
  * If Cloudinary credentials exist: upload images to Cloudinary.
  * If absent or failing: store locally in `backend/static/outputs/` and serve via FastAPI static route.
* **Endpoints**:
  * `POST /api/v1/restore`: Submit async job.
  * `GET /api/v1/restore/{job_id}`: Poll status.
  * `POST /api/v1/restore/sync`: Synchronous execution.
  * `POST /api/v1/identify`: Multipart image upload $\rightarrow$ CLIP gallery identification.
  * `GET /api/v1/history/{monument_id}`: Grounded historical facts.
  * `POST /api/v1/identify-and-inform`: Combined identification + verified history.
  * `GET /health`: Health and model readiness.

---

### PHASE 5: CINEMATIC WEB FRONTEND & MOBILE-FIRST PWA

* **Design Direction**:
  * Strict adherence to approved design system: warm neutrals, serif headings, narrow glass panels, and subtle film grain overlay.
* **Mobile-First PWA Polish**:
  * Installable Web App manifest (`manifest.json` + service worker / PWA meta tags).
  * Camera capture via `<input type="file" accept="image/*" capture="environment">`.
  * Verified and responsive at 390px mobile viewport width.
* **Core Views**:
  * Hero with interactive `<BeforeAfterSlider />`.
  * Full-bleed photo hero result on high confidence; graceful candidate fallback below threshold.
  * Editorial history detail page with interactive timeline and verified source badges.

---

### PHASE 6: MEASURED EVALUATION HARNESS & FINAL REPORTING

* **Measured Benchmarking**:
  * No fixed hypothetical metric targets.
  * Run evaluation harness and report measured PSNR, SSIM, LPIPS, and classifier held-out accuracy, plus the measured delta versus pre-change baselines.
* **Docker Packaging**:
  * Dockerfile and `docker-compose.yml` are optional / stretch. Skip if GPU passthrough is unsupported.
* **Documentation**:
  * Update `README.md` with final measured benchmarks, pipeline diagrams, and quickstart instructions.
