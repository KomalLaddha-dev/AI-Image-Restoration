# 🏛️ MASTER EXECUTION PROMPT: COMPLETE IMPLEMENTATION OF HERITAGE RESTORE

> **Target Project:** Heritage Restore (`f:\AI Image Restoration`)  
> **Objective:** Execute and complete all remaining phases of the project — spanning the **Monument Identification Engine ("The Left Part")**, **RAG Knowledge Base ("The Right Part")**, **Image Restoration Pipeline Hardening**, **Cinematic Web Demo**, and **Automated Benchmark Harness**.

---

## 🎯 MISSION BRIEF & SYSTEM CONTEXT

You are a Senior Full-Stack AI Engineer and Computer Vision Specialist. Your task is to bring the **Heritage Restore** project to 100% completion with a production-grade Web application and FastAPI backend. (Mobile app is explicitly out of scope).

The architecture comprises two tiers beneath the web client application:
1. **Restoration Pipeline**: 5-stage sequential tensor reconstruction (`BOPBTL` Old Photo Repair → `DDColor` Colorize → `NAFNet` Denoise/Deblur → `GFPGAN` Face Restore → `Real-ESRGAN` 4x Upscale).
2. **Dual-Intelligence Knowledge Layer**:
   - **Left Part (Identification)**: Landmark / Monument computer vision recognition from user-uploaded archival or modern photos.
   - **Right Part (Historical Retrieval)**: Grounded RAG (FAISS + all-MiniLM-L6-v2 + Groq Llama 3.3 70B) retrieving strictly cited provenance from curated corpus archives.

Currently, the Restoration Pipeline and Web Demo foundations are laid, but:
- Monument Identification is running on a hardcoded Taj Mahal mock in `backend/app/services/identification_service.py`.
- RAG Corpus only has 3 monuments populated (`taj_mahal`, `colosseum`, `pyramids_giza`).
- Restoration Pipeline has known color/texture issues (Reinhard color grading bleed and NAFNet over-smoothing).

Follow the step-by-step roadmap below to complete the entire codebase.

---

## 📋 STEP-BY-STEP IMPLEMENTATION ROADMAP

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COMPLETION ROADMAP                              │
│                                                                        │
│  Phase 1: Monument Identification Engine ("The Left Part")             │
│  Phase 2: RAG Corpus Expansion & Provenance ("The Right Part")         │
│  Phase 3: Restoration Pipeline Hardening & Quality Fixes               │
│  Phase 4: API & Storage Hardening (Local + Cloudinary Failover)        │
│  Phase 5: Cinematic Web Frontend (Awwwards-Level Polish)               │
│  Phase 6: Evaluation Suite, Tests, Docker & Documentation              │
└────────────────────────────────────────────────────────────────────────┘
```

---

### PHASE 1: MONUMENT IDENTIFICATION ENGINE ("THE LEFT PART")

#### 1.1 Create `backend/app/ml/classifier/monument_classifier.py`
Build a production-grade, two-tier visual recognition engine:
- **Tier 1 (ONNX Fast-Path)**:
  - Load `backend/models/monument_classifier.onnx` using `onnxruntime.InferenceSession`.
  - Input: `(1, 3, 224, 224)` normalized via ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
  - Output: Softmax distribution over classes defined in `backend/models/labels.json`.
- **Tier 2 (Foundation / Visual Embedding Fallback)**:
  - If ONNX weights are not present or confidence is low, extract visual features using `sentence-transformers/clip-ViT-B-32` or pre-computed reference image embeddings from canonical monument samples (`web-demo/public/samples/`).
  - Calculate cosine similarity against monument gallery vectors.
- **Preprocessing for Historical Photographs**:
  - Implement photometric normalization: if the image is sepia or grayscale, apply contrast adjustment / CLAHE so faded photographs match canonical structural features.
  - Return: `(monument_id, monument_name, confidence, top_candidates)`.

#### 1.2 Update `backend/app/services/identification_service.py`
- Eliminate the mock demo block (`demo = list(self._labels.values())[0]`).
- Delegate inference directly to `MonumentClassifier`.
- Join the predicted `monument_id` with `backend/data/monuments.json` to extract `location`, `era`, `coordinates`, and `architectural_style`.
- Enforce strict confidence thresholds:
  - `confidence >= 0.60`: Return `IdentifyResponse` (`recognized=True`).
  - `confidence < 0.60`: Return `IdentifyNotRecognizedResponse` (`recognized=False`, with top-3 candidate suggestions).

#### 1.3 Create Automated Model Bootstrap: `backend/scripts/setup_monument_classifier.py`
- Parse all classes from `backend/data/monuments.json`.
- Automatically generate `backend/models/labels.json`.
- Export a working `monument_classifier.onnx` based on MobileNetV3-Large with transfer learning weights, or compile anchor visual prototypes so the server runs out-of-the-box without requiring Colab training upfront.
- Add self-test verifying inference on `taj_mahal.jpg`, `qutub_minar.jpg`, and `colosseum.jpg`.

---

### PHASE 2: RAG CORPUS & PROVENANCE ("THE RIGHT PART")

#### 2.1 Expand Monument Knowledge Corpus
- Populate `backend/data/corpus/*.json` for all monuments present in `backend/data/monuments.json` (Red Fort, Qutub Minar, Hawa Mahal, India Gate, Colosseum, Eiffel Tower, etc.).
- Structure per file:
  ```json
  {
    "monument_id": "red_fort",
    "name": "Red Fort",
    "location": "Delhi, India",
    "era": "1638–1648 CE",
    "builder": "Emperor Shah Jahan",
    "architectural_style": "Mughal architecture",
    "unesco_status": "World Heritage Site (2007)",
    "chunks": [
      {
        "text": "The Red Fort was commissioned by Emperor Shah Jahan in 1638...",
        "source": "Archaeological Survey of India",
        "source_url": "https://asi.nic.in"
      }
    ]
  }
  ```

#### 2.2 Rebuild FAISS Vector Index
- Create/update `backend/scripts/build_faiss_index.py`:
  - Load all JSON chunks in `backend/data/corpus/`.
  - Embed with `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional).
  - Persist FAISS `IndexFlatIP` to `backend/data/faiss_index.bin` and metadata to `backend/data/faiss_meta.json`.
- Update `backend/app/ml/rag/generator.py`:
  - Ensure zero hallucination prompt: require inline citations `[Source Name]`.
  - Add offline fallback: if `GROQ_API_KEY` is not provided or fails, synthesize a clean summary from curated corpus chunks directly.

---

### PHASE 3: RESTORATION PIPELINE HARDENING & QUALITY FIXES

Address known issues documented in `project_context_fix.md`:

#### 3.1 Reinhard Color Transfer & Foliage Fix (`backend/app/ml/stages/colorize.py`)
- Disable or condition the global Reinhard color transfer that causes foliage discoloration and hazy sepia bleed.
- Default to native DDColor colorization output in LAB color space, preserving natural hues while eliminating the sepia cast.

#### 3.2 Texture Preservation & Denoise Tuning (`backend/app/ml/stages/denoise_deblur.py`)
- Eliminate painterly/smooth artifacts caused by aggressive NAFNet passes.
- Implement adaptive edge-preserving detail blending: blend 20–30% of high-frequency original texture back into the denoised result to preserve authentic photographic film grain.

#### 3.3 Hardware Safety & VRAM Management (`backend/app/ml/pipeline.py`)
- Standardize the auto-downscaling GPU retry logic for 6GB VRAM (e.g., RTX 3050):
  - Attempt stage processing at requested resolution.
  - On `torch.cuda.OutOfMemoryError`, clear cache, downscale to `max_side = 768px`, and retry on GPU.
  - Fall back to CPU only if GPU retry fails.

---

### PHASE 4: API & STORAGE RESILIENCE

#### 4.1 Hybrid Storage Service (`backend/app/services/storage_service.py`)
- If Cloudinary credentials are provided, upload original and restored images to Cloudinary.
- If Cloudinary credentials are empty, save to `backend/static/outputs/` and serve via FastAPI static files (`/static/outputs/...`).

#### 4.2 Verify All Endpoints
- `POST /api/v1/restore`: Submit async restoration job.
- `GET /api/v1/restore/{job_id}`: Poll status, stages applied, and download URLs.
- `POST /api/v1/restore/sync`: Synchronous execution for quick testing.
- `POST /api/v1/identify`: Multipart image upload → returns monument identification.
- `GET /api/v1/history/{monument_id}`: Returns verified history with citations.
- `POST /api/v1/identify-and-inform`: Combined identification + historical summary in a single call.
- `GET /health`: Model availability and health status.

---

### PHASE 5: CINEMATIC WEB DEMO (VITE + REACT)

Elevate `web-demo/` into an award-winning, archival-grade frontend:
- **Art Direction**: Deep dark background (`#0A0A0A`), warm archival gold/amber accents, subtle CSS/SVG film grain overlay.
- **Home (`Home.tsx`)**:
  - Interactive hero section with `<BeforeAfterSlider />`.
  - Quick action buttons: "Restore a Photo" and "Identify a Monument".
  - Curated monument preview cards with confidence badges.
- **Restore Page (`RestorePage.tsx`)**:
  - Drag-and-drop upload zone.
  - Toggles for individual stages: Old Photo Repair, Denoise/Deblur, Face Restore, Colorize, Upscale.
  - Dynamic progress indicator.
  - Interactive comparison slider with full-screen zoom and download button.
- **Identify Page (`IdentifyPage.tsx`)**:
  - Live photo upload / camera capture.
  - High-confidence view (≥70%): full-bleed user photo hero backdrop, glassmorphism metadata card, and "Read Verified History" CTA.
  - Low-confidence view (<70%): helpful fallback card offering candidate guesses and a "Restore Photo First" shortcut.
- **History Detail (`HistoryDetail.tsx`)**:
  - Editorial header, RAG-grounded summary, inline source citations, interactive timeline, and architectural specs.

---

### PHASE 6: BENCHMARKS, TESTING, DOCKER & DOCUMENTATION

#### 6.1 Automated Benchmarking Harness
- Run evaluation scripts:
  ```bash
  python backend/scripts/generate_taj_report.py
  python backend/app/eval/run_eval.py
  ```
- Target metrics: PSNR > 28 dB, SSIM > 0.85, LPIPS < 0.15, Classifier Top-1 Accuracy > 90%.

#### 6.2 Pytest Suite
Create and pass tests in `backend/tests/`:
- `test_restore.py`: Validates single and multi-stage restoration pipelines.
- `test_identify.py`: Tests clear photos, degraded photos, and out-of-distribution inputs.
- `test_rag.py`: Tests embedding retrieval and generator citations.
- `test_combined.py`: Tests `/identify-and-inform` integration.

#### 6.3 Production Docker Setup
- Create root `docker-compose.yml` orchestrating:
  - `backend`: Python 3.12, PyTorch, Uvicorn on port 8000.
  - `web-demo`: Nginx / Vite preview on port 5173.

#### 6.4 Documentation
- Update `README.md` with:
  - Architecture diagram reflecting both the Restoration Pipeline and the Dual Intelligence Layer.
  - Swagger UI guide (`http://localhost:8000/docs`).
  - Web demo setup and quickstart instructions.

---

## ⚡ EXECUTION INSTRUCTIONS FOR THE AGENT

1. Begin with **Phase 1**: implement `monument_classifier.py`, wire real inference in `identification_service.py`, and run `setup_monument_classifier.py`.
2. Proceed to **Phase 2**: populate missing corpus files in `backend/data/corpus/` and index them with FAISS.
3. Execute **Phase 3**: refine DDColor colorization and NAFNet edge-blending in the restoration stages.
4. Verify **Phase 4 & 5**: launch FastAPI and Vite dev server to validate the full workflow in browser.
5. Complete **Phase 6**: execute test suite and output final benchmark results.
