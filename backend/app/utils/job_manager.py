"""
In-memory job manager for tracking restoration job status.
In production, replace with Redis or database-backed storage.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from app.models.schemas import JobStatus, RestoreResultResponse, StageResult


class JobManager:
    """Thread-safe in-memory job tracker."""

    def __init__(self):
        self._jobs: dict[str, RestoreResultResponse] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, job_id: str) -> RestoreResultResponse:
        """Register a new pending job."""
        async with self._lock:
            job = RestoreResultResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            self._jobs[job_id] = job
            logger.info(f"Job created: {job_id}")
            return job

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        **kwargs: Any,
    ) -> None:
        """Update a job's status and optional fields."""
        async with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Job {job_id} not found")
            job = self._jobs[job_id]
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now(timezone.utc)
            logger.info(f"Job {job_id} → {status.value}")

    async def add_stage_result(self, job_id: str, stage: StageResult) -> None:
        """Append a stage result to the job."""
        async with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Job {job_id} not found")
            self._jobs[job_id].stages_applied.append(stage)

    async def get_job(self, job_id: str) -> RestoreResultResponse | None:
        """Retrieve a job by ID."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 50) -> list[RestoreResultResponse]:
        """List recent jobs."""
        async with self._lock:
            jobs = sorted(
                self._jobs.values(),
                key=lambda j: j.created_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            return jobs[:limit]


# Global singleton
job_manager = JobManager()
