"""
Restore API routes — POST /restore, GET /restore/{job_id}
"""

from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from loguru import logger

from app.models.schemas import (
    JobStatus,
    RestoreJobResponse,
    RestoreOptions,
    RestoreResultResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Restoration"])


@router.post(
    "/restore",
    response_model=RestoreJobResponse,
    summary="Submit an image for restoration",
    description="Upload a degraded historical photo for AI-powered restoration. "
    "Returns a job_id for async polling.",
)
async def restore_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP)"),
    options: str = Form(
        default="{}",
        description='JSON string of RestoreOptions, e.g. {"stages": ["denoise","upscale"]}',
    ),
):
    """Submit an image restoration job."""
    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    # Read image data
    image_data = await file.read()
    if len(image_data) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if len(image_data) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")

    # Parse options
    try:
        opts_dict = json.loads(options)
        restore_options = RestoreOptions(**opts_dict)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Invalid restore options: {e}, using defaults")
        restore_options = RestoreOptions()

    # Get the restoration service from app state
    from app.main import get_restoration_service
    service = get_restoration_service()

    # Submit job
    job = await service.submit_job(image_data, file.filename or "upload.png", restore_options)

    # Run restoration in background
    background_tasks.add_task(
        service.process_job,
        job.job_id,
        image_data,
        restore_options,
    )

    logger.info(f"Restoration job submitted: {job.job_id} (stages: {restore_options.stages})")
    return job


@router.get(
    "/restore/{job_id}",
    response_model=RestoreResultResponse,
    summary="Get restoration job status/result",
    description="Poll for the status of a restoration job. "
    "Returns image URLs when complete.",
)
async def get_restore_result(job_id: str):
    """Poll restoration job status."""
    from app.main import get_restoration_service
    service = get_restoration_service()

    result = await service.get_job_status(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return result


@router.post(
    "/restore/sync",
    summary="Restore an image synchronously (blocking)",
    description="For small images: upload → wait → get restored image directly. "
    "Blocks until restoration is complete.",
)
async def restore_image_sync(
    file: UploadFile = File(...),
    options: str = Form(default="{}"),
):
    """Synchronous restoration — blocks until done, returns image bytes."""
    from fastapi.responses import Response

    image_data = await file.read()
    if len(image_data) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        opts_dict = json.loads(options)
        restore_options = RestoreOptions(**opts_dict)
    except Exception:
        restore_options = RestoreOptions()

    from app.main import get_restoration_service
    service = get_restoration_service()

    restored_bytes, stages, total_ms = await service.process_sync(image_data, restore_options)

    return Response(
        content=restored_bytes,
        media_type="image/png",
        headers={
            "X-Processing-Time-Ms": str(total_ms),
            "X-Stages-Applied": ",".join(s.stage for s in stages if s.applied),
        },
    )
