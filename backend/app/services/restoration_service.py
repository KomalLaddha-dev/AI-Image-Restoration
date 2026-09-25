"""
Restoration service — business logic layer between API routes and ML pipeline.
Handles image I/O, job management, and storage.
"""

from __future__ import annotations

import uuid
import tempfile
from pathlib import Path

import numpy as np
from loguru import logger

from app.config import get_settings
from app.models.schemas import (
    JobStatus,
    RestoreOptions,
    RestoreJobResponse,
    RestoreResultResponse,
    StageResult,
)
from app.ml.pipeline import RestorationPipeline
from app.utils.image_utils import load_image_from_bytes, save_image_to_bytes, save_image_to_file
from app.utils.job_manager import job_manager


class RestorationService:
    """Coordinates image restoration: receives uploads, runs pipeline, stores results."""

    def __init__(self, pipeline: RestorationPipeline):
        self.pipeline = pipeline
        self.output_dir = Path(tempfile.gettempdir()) / "heritage_restore"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def submit_job(
        self,
        image_data: bytes,
        filename: str,
        options: RestoreOptions | None = None,
    ) -> RestoreJobResponse:
        """
        Submit a new restoration job.
        Returns immediately with a job_id; restoration runs in the background.
        """
        job_id = str(uuid.uuid4())
        await job_manager.create_job(job_id)

        # Save original image
        original_path = self.output_dir / f"{job_id}_original.png"
        img = load_image_from_bytes(image_data)
        save_image_to_file(img, original_path)

        return RestoreJobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message=f"Job submitted. Original saved as {filename}.",
        )

    async def process_job(
        self,
        job_id: str,
        image_data: bytes,
        options: RestoreOptions | None = None,
    ) -> RestoreResultResponse:
        """
        Execute the restoration pipeline for a submitted job.
        This is called from a background task.
        """
        try:
            await job_manager.update_status(job_id, JobStatus.PROCESSING)

            # Load and restore
            img = load_image_from_bytes(image_data)
            result = await self.pipeline.restore(img, options)

            # Save restored image
            restored_path = self.output_dir / f"{job_id}_restored.png"
            save_image_to_file(result.restored, restored_path)

            original_path = self.output_dir / f"{job_id}_original.png"

            # Update job with results
            await job_manager.update_status(
                job_id,
                JobStatus.COMPLETED,
                original_url=f"/static/restore/{job_id}_original.png",
                restored_url=f"/static/restore/{job_id}_restored.png",
                stages_applied=result.stage_results,
                total_processing_time_ms=result.total_time_ms,
                warnings=result.warnings,
            )

            return await job_manager.get_job(job_id)

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await job_manager.update_status(
                job_id,
                JobStatus.FAILED,
                error_message=str(e),
            )
            return await job_manager.get_job(job_id)

    async def process_sync(
        self,
        image_data: bytes,
        options: RestoreOptions | None = None,
    ) -> tuple[bytes, list[StageResult], int]:
        """
        Synchronous restoration — blocks until done.
        For small images or when the caller wants the result immediately.

        Returns:
            (restored_image_bytes, stage_results, total_time_ms)
        """
        img = load_image_from_bytes(image_data)
        result = await self.pipeline.restore(img, options)
        restored_bytes = save_image_to_bytes(result.restored, ".png")
        return restored_bytes, result.stage_results, result.total_time_ms

    async def get_job_status(self, job_id: str) -> RestoreResultResponse | None:
        """Get the current status of a restoration job."""
        return await job_manager.get_job(job_id)
