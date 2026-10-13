"""
Unit & Integration Tests for Monument Identification
======================================================
Tests:
- Identification of clear monument photos (Taj Mahal, Colosseum, Qutub Minar, Pyramids).
- Robustness on degraded historical photos (Taj Mahal hero degraded).
- Rejection of out-of-distribution / non-monument photographs.
- FastAPI endpoint `/api/v1/identify`.
"""

from pathlib import Path
import cv2
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.identification_service import IdentificationService
from app.models.schemas import IdentifyResponse, IdentifyNotRecognizedResponse

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "web-demo" / "public" / "samples"


@pytest.fixture
def service():
    srv = IdentificationService()
    srv.load()
    return srv


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_taj_mahal_clean(service):
    img_path = SAMPLES_DIR / "taj_mahal.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "taj_mahal"
    assert result.monument_name == "Taj Mahal"
    assert result.confidence >= 0.70
    assert result.location is not None


@pytest.mark.asyncio
async def test_taj_mahal_degraded(service):
    img_path = SAMPLES_DIR / "taj_mahal_hero_degraded.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "taj_mahal"
    assert result.confidence >= 0.60


@pytest.mark.asyncio
async def test_colosseum(service):
    img_path = SAMPLES_DIR / "colosseum.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "colosseum"
    assert result.confidence >= 0.70


@pytest.mark.asyncio
async def test_qutub_minar(service):
    img_path = SAMPLES_DIR / "qutub_minar.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "qutub_minar"
    assert result.confidence >= 0.70


@pytest.mark.asyncio
async def test_pyramids(service):
    img_path = SAMPLES_DIR / "pyramids_giza.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyResponse)
    assert result.recognized is True
    assert result.monument_id == "pyramids_giza"
    assert result.confidence >= 0.70


@pytest.mark.asyncio
async def test_out_of_distribution_rejection(service):
    img_path = SAMPLES_DIR / "detroit_1915.jpg"
    assert img_path.exists(), f"Sample not found: {img_path}"

    img = cv2.imread(str(img_path))
    result = await service.identify(img)

    assert isinstance(result, IdentifyNotRecognizedResponse)
    assert result.recognized is False
    assert result.confidence < 0.60
    assert len(result.suggestions) > 0


def test_api_endpoint_identify(client):
    img_path = SAMPLES_DIR / "taj_mahal.jpg"
    with open(img_path, "rb") as f:
        response = client.post(
            "/api/v1/identify",
            files={"file": ("taj_mahal.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is True
    assert data["monument_id"] == "taj_mahal"
    assert data["confidence"] >= 0.70


def test_api_endpoint_identify_ood(client):
    img_path = SAMPLES_DIR / "detroit_1915.jpg"
    with open(img_path, "rb") as f:
        response = client.post(
            "/api/v1/identify",
            files={"file": ("detroit_1915.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is False
    assert data["confidence"] < 0.60
    assert "suggestions" in data
