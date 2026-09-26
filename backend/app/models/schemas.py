"""
Pydantic request/response schemas for all API endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RestorationMode(str, Enum):
    STANDARD = "standard"
    PORTRAIT = "portrait"
    COLORIZE = "colorize"
    ADVANCED = "advanced"

class ColorizationMode(str, Enum):
    AUTO = "auto"
    FORCE = "force"
    OFF = "off"


class RestorationStage(str, Enum):
    OLD_PHOTO_REPAIR = "old_photo_repair"
    DENOISE = "denoise"
    FACE_RESTORE = "face_restore"
    COLORIZE = "colorize"
    UPSCALE = "upscale"


# ─── Restoration ──────────────────────────────────────────────────────────────

class RestoreOptions(BaseModel):
    """Options sent with a restoration request."""
    face_restore: bool = Field(default=False, description="Enable face restoration (GFPGAN)")
    colorize: bool = Field(default=False, description="Enable colorization (DDColor)")
    colorization_mode: ColorizationMode = Field(default=ColorizationMode.AUTO, description="auto, force, or off")
    denoise: bool = Field(default=False, description="Enable denoising/deblurring (NAFNet)")
    mode: RestorationMode = Field(
        default=RestorationMode.STANDARD,
        description="Standard, portrait, colorize, or advanced.",
    )


class StageResult(BaseModel):
    """Result of a single pipeline stage."""
    stage: str
    processing_time_ms: int
    applied: bool = True


class RestoreJobResponse(BaseModel):
    """Response after submitting a restore job."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    message: str = "Job submitted successfully."


class RestoreResultResponse(BaseModel):
    """Response when polling for a completed job."""
    job_id: str
    status: JobStatus
    original_url: str | None = None
    restored_url: str | None = None
    stages_applied: list[StageResult] = []
    total_processing_time_ms: int = 0
    created_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    warnings: list[str] = []


# ─── Monument Identification ─────────────────────────────────────────────────

class IdentifyResponse(BaseModel):
    """Response after identifying a monument from an image."""
    monument_id: str
    monument_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    location: str | None = None
    era: str | None = None
    thumbnail_url: str | None = None
    recognized: bool = True


class IdentifyNotRecognizedResponse(BaseModel):
    """Response when the monument isn't recognized."""
    recognized: bool = False
    message: str = "This monument is not in our database yet."
    confidence: float = 0.0
    suggestions: list[str] = []


# ─── Historical Information ──────────────────────────────────────────────────

class SourceCitation(BaseModel):
    """A single source citation for a historical fact."""
    name: str
    url: str | None = None


class TimelineEvent(BaseModel):
    """A single event in the monument's timeline."""
    year: str
    event: str


class HistoryResponse(BaseModel):
    """Full historical info card for a monument."""
    monument_id: str
    name: str
    summary: str
    era: str | None = None
    builder: str | None = None
    architectural_style: str | None = None
    unesco_status: str | None = None
    location: str | None = None
    coordinates: list[float] | None = None
    sources: list[SourceCitation] = []
    timeline: list[TimelineEvent] = []
    related_images: list[dict] = []


# ─── Combined Endpoint ───────────────────────────────────────────────────────

class IdentifyAndInformResponse(BaseModel):
    """Combined identification + history in one call."""
    identification: IdentifyResponse | IdentifyNotRecognizedResponse
    history: HistoryResponse | None = None


# ─── Health Check ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Server health check response."""
    status: str = "ok"
    environment: str = "development"
    models_loaded: list[str] = []
    uptime_seconds: float = 0.0
