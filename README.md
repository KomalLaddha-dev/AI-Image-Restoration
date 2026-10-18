# 🏛️ Heritage Restore — AI Image Restoration & Monument Provenance

> High-fidelity restoration of damaged historical photographs paired with CLIP-powered monument identification and verified archival provenance.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PyTorch](https://img.shields.io/badge/PyTorch-2.6-red)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Vite](https://img.shields.io/badge/Vite-6.0-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        HERITAGE RESTORE SYSTEM                         │
├──────────────────────────────────┬─────────────────────────────────────┤
│  1. Monument Identification      │  2. Historical RAG Knowledge Base   │
│  • CLIP (clip-ViT-B-32)          │  • Verified Wikipedia Corpora       │
│  • Softmax (tau=0.03, T=0.65)    │  • FAISS (all-MiniLM-L6-v2) Index   │
│  • 12 Heritage Landmarks         │  • Groq Qwen/Llama + JSON Fallback  │
├──────────────────────────────────┴─────────────────────────────────────┤
│  3. Multi-Stage Heritage Restoration Pipeline (max_side=768, HR=False) │
│  [Crack Inpaint]  ──> [BOPBTL Global] ──> [DDColor LAB] ──> [ESRGAN]   │
│  (LaMa Inpaint)       (Old Photo GAN)    (Neutral Luma)     (2x / 4x)  │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Monument Recognition ("The Left Part")
- **Primary Engine**: OpenAI CLIP (`clip-ViT-B-32`) visual embeddings with precomputed reference gallery.
- **Calibrated Scoring**: Temperature-scaled ($\tau = 0.03$) softmax across monument classes with a unified threshold ($T = 0.65$).
- **Held-Out Test Performance**: 86.5% Precision, 80.4% Recall, 83.3% F1, 85.0% Out-of-Distribution Rejection across 80 held-out images.

### 2. Verified Knowledge Base ("The Right Part")
- **Archival Corpus**: 12 curated historical landmarks with Wikipedia `CC BY-SA` citations and verified facts.
- **Retriever**: FAISS dense vector search over verified chunks with `sentence-transformers/all-MiniLM-L6-v2`.
- **Grounded Provenance**: Groq LLM synthesis with graceful fallback to structured JSON facts when an API key is absent.

### 3. Restoration Pipeline Overhaul
- **Crack Inpainting**: Extracts BOPBTL scratch mask at $\le 768$px, dilates 5px, and inpaints using SimpleLama (`cv2.inpaint` fallback).
- **Old Photo Repair**: Microsoft Bringing-Old-Photos-Back-to-Life with GPU OOM safety nets.
- **Native LAB Colorization**: DDColor color inference stitched strictly with neutral input luminance to avoid sepia bleed.
- **Texture Preservation**: NAFNet disabled by default (`denoise_strength=0.0`) to preserve historical stone and carving textures.

---

## 🚀 Setup & Execution on a New Device

Follow these steps to run the complete project on any computer:

### Prerequisites
- **Git**
- **Python 3.10 – 3.12**
- **Node.js 18+ & npm**
- *(Optional)* NVIDIA GPU with CUDA for accelerated neural inference. (CPU fallback is automatically supported).

---

### Step 1: Clone the Repository
```bash
git clone <repo-url>
cd "AI Image Restoration"
```

---

### Step 2: Backend Setup (Python)

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

# 2. Install Python dependencies (NumPy pinned to 1.26.4 for SimpleLama compatibility)
pip install -r requirements.txt

# 3. Download pretrained models and setup BOPBTL checkpoints (Automated)
python scripts/download_models.py

# 4. (Optional) Configure environment variables
# Copy template and optionally add your GROQ_API_KEY for dynamic RAG generation
copy .env.example .env
```

#### Start the Backend API Server:
```bash
uvicorn app.main:app --reload --port 8000
```
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 3: Web Demo Setup (React + Vite)

Open a **second terminal**:

```bash
cd web-demo

# Install frontend dependencies
npm install

# Start the Vite development server
npm run dev
```
- **Web Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Automated Tests

To run the complete automated test suite (19 test cases covering CLIP identification, out-of-distribution rejection, RAG retriever precision, Groq fallback, and image quality checks):

```bash
cd backend
python -m pytest tests/ -v
```

---

## 📡 Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/identify` | Multipart photo upload $\rightarrow$ CLIP gallery identification & confidence |
| `GET` | `/api/v1/history/{monument_id}` | Grounded historical facts & verified Wikipedia provenance |
| `POST` | `/api/v1/identify-and-inform` | Combined landmark recognition + archival history in one call |
| `POST` | `/api/v1/restore` | Submit async image restoration job |
| `GET` | `/api/v1/restore/{job_id}` | Poll restoration status and download URLs |
| `POST` | `/api/v1/restore/sync` | Synchronous restoration returning processed image bytes directly |
| `GET` | `/health` | Server status and loaded ML models |

---

## 📊 Measured Restoration Benchmark

Evaluated on synthetic degraded historical photographs with crack masks:

| Metric | Degraded Baseline | AI Restored | Measured Delta |
|---|---|---|---|
| **Luminance PSNR** | 20.54 dB | **22.89 dB** | **+2.35 dB** |
| **Luminance SSIM** | 0.5301 | **0.8154** | **+0.2853** |
| **Colour PSNR** | 17.66 dB | **19.08 dB** | **+1.42 dB** |
| **Colour SSIM** | 0.4590 | **0.7435** | **+0.2845** |
| **LPIPS Distance (↓)** | 0.8235 | **0.4387** | **-0.3848** (perceptual gain) |
| **Crack Edge Energy** | 1.0000 | **0.2074** | **79.3% reduction** |
