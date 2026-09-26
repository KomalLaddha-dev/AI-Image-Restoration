"""
Heritage Restore — AI-Based Historical Image Restoration & Information Retrieval

FastAPI application entry point with lifespan events for model loading/unloading.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

import torch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import get_settings
from app.api.router import api_router
from app.ml.pipeline import RestorationPipeline
from app.ml.rag.embedder import Embedder
from app.ml.rag.retriever import Retriever
from app.ml.rag.generator import Generator
from app.services.restoration_service import RestorationService
from app.services.identification_service import IdentificationService
from app.models.schemas import HealthResponse


# ── Global service instances (initialized in lifespan) ────────────────────────
_restoration_service: RestorationService | None = None
_identification_service: IdentificationService | None = None
_retriever: Retriever | None = None
_generator: Generator | None = None
_start_time: float = 0.0
_pipeline: RestorationPipeline | None = None


def get_restoration_service() -> RestorationService:
    assert _restoration_service is not None, "Restoration service not initialized"
    return _restoration_service


def get_identification_service() -> IdentificationService:
    assert _identification_service is not None, "Identification service not initialized"
    return _identification_service


def get_rag_components() -> tuple[Retriever, Generator]:
    assert _retriever is not None and _generator is not None, "RAG not initialized"
    return _retriever, _generator


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — load and unload ML models."""
    global _restoration_service, _identification_service
    global _retriever, _generator, _start_time, _pipeline

    settings = get_settings()
    _start_time = time.time()
    logger.info(f"🏛️ Heritage Restore starting (env={settings.app_env})")
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA available: {cuda_available}")
    if cuda_available:
        logger.info(f"GPU name: {torch.cuda.get_device_name(0)}")
        if hasattr(torch.version, 'cuda'):
            logger.info(f"torch.version.cuda: {torch.version.cuda}")

    # 1. Initialize restoration pipeline and preload ALL models
    _pipeline = RestorationPipeline()
    logger.info("⏳ Preloading all ML models (DDColor, NAFNet, Real-ESRGAN, GFPGAN, BOPBTL)...")
    _pipeline.preload()
    logger.info("✅ All ML models preloaded — ready for requests")

    _restoration_service = RestorationService(_pipeline)

    # 2. Initialize monument identification
    _identification_service = IdentificationService()
    _identification_service.load()

    # 3. Initialize RAG components
    embedder = Embedder()
    _retriever = Retriever(embedder)
    _generator = Generator()

    # Load corpus if available
    corpus_dir = Path("data") / "corpus"
    if corpus_dir.exists():
        _retriever.load(corpus_dir)
    else:
        logger.warning(f"Corpus directory not found: {corpus_dir}")

    # Ensure static directory exists for serving restored images
    static_dir = Path("static") / "restore"
    static_dir.mkdir(parents=True, exist_ok=True)

    logger.info("✅ All services initialized")
    yield

    # Shutdown
    logger.info("🛑 Shutting down — unloading models...")
    if _pipeline:
        _pipeline.unload_all()
    logger.info("Shutdown complete")


# ── App Creation ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Heritage Restore API",
        description=(
            "AI-powered restoration and enhancement of ancient historical images, "
            "with mobile-based monument identification and historical information retrieval."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.0f}ms)"
        )
        return response

    # Static files for serving restored images
    static_dir = Path("static")
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # API routes
    app.include_router(api_router)

    # Health check
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Server health check with loaded model info."""
        return HealthResponse(
            status="ok",
            environment=settings.app_env,
            models_loaded=_pipeline.get_loaded_models() if _pipeline else [],
            uptime_seconds=time.time() - _start_time,
        )

    # Root redirect
    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": "Heritage Restore API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# ── Entry Point ───────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level="info",
    )
