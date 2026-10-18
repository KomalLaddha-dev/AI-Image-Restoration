"""
Unit & Integration Tests for Monument Identification
======================================================
Tests the CLIP (clip-ViT-B-32) + Reference Gallery identification engine
on strictly held-out test photos (zero overlap with gallery images):
- Clean held-out monument photos (Taj Mahal, Colosseum, Qutub Minar, Pyramids).
- Degraded / sepia held-out photo (Taj Mahal degraded).
- Out-of-distribution rejection:
    (a) Non-monument photos (Detroit 1915 street scene, everyday objects).
    (b) Monuments NOT in the gallery (Big Ben).
- FastAPI endpoints:
    - `/api/v1/identify`
    - `/api/v1/identify-and-inform`
"""

from pathlib import Path
import cv2
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.identification_service import IdentificationService, CONFIDENCE_THRESHOLD
from app.models.schemas import IdentifyResponse, IdentifyNotRecognizedResponse

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "test_set"


@pytest.fixture
def service():
    srv = IdentificationService()
    srv.load()
    return srv


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.mark.asyncio
async def test_taj_mahal_clean(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "taj_mahal" / "test_clean_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "taj_mahal"
    assert result.monument_name == "Taj Mahal"
    assert result.confidence >= CONFIDENCE_THRESHOLD
    assert result.location is not None


@pytest.mark.asyncio
async def test_taj_mahal_degraded(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "taj_mahal" / "test_degraded_sepia_scratches.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "taj_mahal"
    assert result.confidence >= CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_red_fort_clean(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "red_fort" / "test_clean_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "red_fort"
    assert result.monument_name == "Red Fort"
    assert result.confidence >= CONFIDENCE_THRESHOLD
    assert result.location is not None


@pytest.mark.asyncio
async def test_red_fort_degraded(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "red_fort" / "test_degraded_sepia_scratches.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "red_fort"
    assert result.confidence >= CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_colosseum_clean(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "colosseum" / "test_clean_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "colosseum"
    assert result.confidence >= CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_qutub_minar_clean(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "qutub_minar" / "test_clean_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "qutub_minar"
    assert result.confidence >= CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_pyramids_clean(service):
    img_path = TEST_DATA_DIR / "in_gallery" / "pyramids_giza" / "test_clean_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "pyramids_giza"
    assert result.confidence >= CONFIDENCE_THRESHOLD


@pytest.mark.asyncio
async def test_non_monument_rejection(service):
    img_path = TEST_DATA_DIR / "non_monuments" / "detroit_1915.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyNotRecognizedResponse)
    assert result.recognized is False
    assert result.confidence < CONFIDENCE_THRESHOLD
    assert len(result.suggestions) > 0


@pytest.mark.asyncio
async def test_unseen_monument_rejection(service):
    img_path = TEST_DATA_DIR / "unseen_monuments" / "big_ben" / "test_1.jpg"
    assert img_path.exists(), f"Held-out test image not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyNotRecognizedResponse)
    assert result.recognized is False
    assert result.confidence < CONFIDENCE_THRESHOLD


def test_api_endpoint_identify(client):
    img_path = TEST_DATA_DIR / "in_gallery" / "taj_mahal" / "test_clean_1.jpg"
    assert img_path.exists()
    with open(img_path, "rb") as f:
        response = client.post(
            "/api/v1/identify",
            files={"file": ("test_clean_1.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is True
    assert data["monument_id"] == "taj_mahal"
    assert data["confidence"] >= CONFIDENCE_THRESHOLD


def test_api_endpoint_identify_ood(client):
    img_path = TEST_DATA_DIR / "non_monuments" / "detroit_1915.jpg"
    assert img_path.exists()
    with open(img_path, "rb") as f:
        response = client.post(
            "/api/v1/identify",
            files={"file": ("detroit_1915.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is False
    assert data["confidence"] < CONFIDENCE_THRESHOLD
    assert "suggestions" in data


def test_api_endpoint_identify_and_inform(client):
    img_path = TEST_DATA_DIR / "in_gallery" / "taj_mahal" / "test_clean_1.jpg"
    assert img_path.exists()
    with open(img_path, "rb") as f:
        response = client.post(
            "/api/v1/identify-and-inform",
            files={"file": ("test_clean_1.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "identification" in data
    assert data["identification"]["recognized"] is True
    assert data["identification"]["monument_id"] == "taj_mahal"
    assert "history" in data
    if data["history"]:
        assert data["history"]["monument_id"] == "taj_mahal"
