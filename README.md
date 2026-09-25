# 🏛️ Heritage Restore — AI Image Restoration & Historical Information Retrieval

> AI-powered restoration of ancient/degraded historical photographs + mobile-based monument identification with verified historical information retrieval.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5-red)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### 🖼️ Image Restoration Pipeline
- **5-stage ML pipeline**: Old photo repair → Denoise/Deblur → Face restore → Colorize → Upscale
- **Models**: Real-ESRGAN, GFPGAN, DDColor, NAFNet + classical CV fallbacks
- **Toggleable stages**: Enable/disable any stage per request
- **Before/after comparison**: Visual side-by-side slider

### 🏛️ Monument Recognition
- **MobileNetV3-Large**: Fine-tuned classifier for 50+ India + World landmarks
- **Confidence thresholding**: Graceful "not recognized" handling
- **ONNX Runtime**: Fast inference for production

### 📚 Historical Information (RAG)
- **Grounded generation**: Groq LLama 3.3 70B — never invents facts
- **FAISS vector search**: Fast retrieval over curated corpus
- **Source citations**: Every fact traced to Wikipedia, UNESCO, ASI, etc.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (for web demo)
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy env and add your API keys
copy .env.example .env
# Edit .env with your GROQ_API_KEY, etc.

# Download model weights
python scripts/download_models.py

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Web Demo Setup

```bash
cd web-demo
npm install
npm run dev
```

### API Documentation
Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/restore` | Submit image for restoration (async) |
| `GET` | `/api/v1/restore/{job_id}` | Poll restoration status/result |
| `POST` | `/api/v1/restore/sync` | Synchronous restoration (blocking) |
| `POST` | `/api/v1/identify` | Identify a monument from a photo |
| `GET` | `/api/v1/history/{monument_id}` | Get historical info with citations |
| `POST` | `/api/v1/identify-and-inform` | Combined: identify + history in one call |
| `GET` | `/health` | Server health check |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────────────┐
│  Web Demo       │────▶│  FastAPI Backend (Python 3.12)   │
│  (Vite + React) │     │                                  │
├─────────────────┤     │  ┌──────────────────────────────┐│
│  Mobile App     │────▶│  │ Restoration Pipeline         ││
│  (Expo / RN)    │     │  │ Old Photo → Denoise → Face   ││
└─────────────────┘     │  │ → Colorize → Upscale         ││
                        │  └──────────────────────────────┘│
                        │  ┌────────────┐ ┌───────────────┐│
                        │  │ MobileNet  │ │ RAG: FAISS +  ││
                        │  │ Classifier │ │ Groq LLM      ││
                        │  └────────────┘ └───────────────┘│
                        └──────────────────────────────────┘
```

---

## 📂 Project Structure

```
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── ml/        # ML pipeline stages + RAG
│   │   ├── models/    # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── utils/     # Image utils, job manager
│   └── scripts/       # Model download, corpus builder
├── classifier-training/  # Colab-ready training scripts
├── data/              # Monument metadata + RAG corpus
├── web-demo/          # Vite + React frontend
└── mobile/            # React Native (Expo) app
```

---

## 🧠 ML Models Used

| Stage | Model | Source |
|-------|-------|--------|
| Old Photo Repair | Classical CV (scratch detect + inpaint + CLAHE) | OpenCV |
| Denoise/Deblur | NAFNet-REDS-width64 | megvii-research |
| Face Restore | GFPGAN v1.4 | TencentARC |
| Colorize | DDColor | piddnad |
| Upscale | Real-ESRGAN x4plus | xinntao |
| Monument ID | MobileNetV3-Large (fine-tuned) | torchvision |
| Embeddings | all-MiniLM-L6-v2 | sentence-transformers |
| RAG Generation | Llama 3.3 70B via Groq | Groq |

---

## 📊 Evaluation Targets

| Metric | Target |
|--------|--------|
| PSNR | > 28 dB |
| SSIM | > 0.85 |
| LPIPS | < 0.15 |
| Classifier Top-1 | > 90% |
| RAG Accuracy | 100% (no hallucination) |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Komal** — Built as an academic portfolio project demonstrating ML, computer vision, NLP, and full-stack development.
