"""
Combined endpoint — POST /identify-and-inform
Identifies a monument AND retrieves its historical information in one call.
This is the main mobile app flow.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from app.models.schemas import (
    IdentifyAndInformResponse,
    IdentifyNotRecognizedResponse,
    IdentifyResponse,
)
from app.utils.image_utils import load_image_from_bytes

router = APIRouter(prefix="/api/v1", tags=["Combined"])


@router.post(
    "/identify-and-inform",
    response_model=IdentifyAndInformResponse,
    summary="Identify a monument and get its history in one call",
    description="Upload a photo → monument identification → historical info. "
    "The primary mobile app endpoint for the 'Identify Monument' flow.",
)
async def identify_and_inform(
    file: UploadFile = File(..., description="Photo of a monument"),
):
    """Combined identify + history endpoint."""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    image_data = await file.read()
    if len(image_data) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    image = load_image_from_bytes(image_data)

    # Step 1: Identify
    from app.main import get_identification_service
    identification_service = get_identification_service()
    identification = await identification_service.identify(image)

    # If not recognized, return early — no history
    if isinstance(identification, IdentifyNotRecognizedResponse) or not identification.recognized:
        return IdentifyAndInformResponse(
            identification=identification,
            history=None,
        )

    # Step 2: Get history
    history = None
    try:
        from app.api.history import get_monument_history
        history = await get_monument_history(identification.monument_id)
    except HTTPException:
        logger.warning(f"No history found for {identification.monument_id}")
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")

    return IdentifyAndInformResponse(
        identification=identification,
        history=history,
    )
