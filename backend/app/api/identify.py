"""
Identify API routes — POST /identify
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from app.models.schemas import IdentifyResponse, IdentifyNotRecognizedResponse
from app.utils.image_utils import load_image_from_bytes

router = APIRouter(prefix="/api/v1", tags=["Monument Identification"])


@router.post(
    "/identify",
    response_model=IdentifyResponse | IdentifyNotRecognizedResponse,
    summary="Identify a monument from a photo",
    description="Upload a photo of a monument/landmark. The AI classifier will "
    "identify it and return metadata. Returns 'not recognized' if confidence is below threshold.",
)
async def identify_monument(
    file: UploadFile = File(..., description="Photo of a monument (JPEG, PNG, WebP)"),
):
    """Identify a monument from an uploaded image."""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    image_data = await file.read()
    if len(image_data) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    image = load_image_from_bytes(image_data)

    from app.main import get_identification_service
    service = get_identification_service()

    result = await service.identify(image)
    logger.info(
        f"Identification result: {getattr(result, 'monument_name', 'not recognized')} "
        f"(confidence: {result.confidence:.2f})"
    )
    return result
