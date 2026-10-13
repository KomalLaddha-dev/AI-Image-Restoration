"""
Monument identification service — wraps the ONNX classifier,
enriches predictions with archival metadata, and provides fallback handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from app.config import get_settings
from app.models.schemas import IdentifyResponse, IdentifyNotRecognizedResponse
from app.ml.classifier.monument_classifier import MonumentClassifier


# Confidence threshold — below this, return "not recognized"
CONFIDENCE_THRESHOLD = 0.60


class IdentificationService:
    """Identifies monuments from images using the MobileNetV3 ONNX classifier."""

    def __init__(self):
        self._classifier: MonumentClassifier | None = None
        self._monument_metadata: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load the monument classifier and metadata mapping."""
        settings = get_settings()
        self._classifier = MonumentClassifier(model_dir=settings.model_dir)
        success = self._classifier.load()

        if success:
            logger.info("Monument classifier ONNX model loaded successfully.")
        else:
            logger.warning("Monument classifier ONNX model could not be loaded at startup.")

        # Load rich metadata from backend/data/monuments.json
        data_path = Path("data") / "monuments.json"
        if not data_path.exists():
            data_path = Path(__file__).resolve().parent.parent.parent / "data" / "monuments.json"

        if data_path.exists():
            try:
                with open(data_path, encoding="utf-8") as f:
                    monuments = json.load(f)
                self._monument_metadata = {m["id"]: m for m in monuments}
                logger.info(f"Loaded {len(self._monument_metadata)} monument metadata records from {data_path.name}")
            except Exception as e:
                logger.warning(f"Failed to load monuments metadata: {e}")

        self._loaded = True
        logger.info("Identification service fully initialized.")

    async def identify(
        self, image: np.ndarray
    ) -> IdentifyResponse | IdentifyNotRecognizedResponse:
        """
        Identify a monument from an uploaded image.

        Returns:
            IdentifyResponse if confidence >= 0.60,
            IdentifyNotRecognizedResponse otherwise.
        """
        if not self._loaded or self._classifier is None:
            self.load()

        if self._classifier is None or not self._classifier.is_loaded:
            logger.error("Classifier is not loaded; cannot run inference.")
            return IdentifyNotRecognizedResponse(
                confidence=0.0,
                suggestions=[],
                message="Identification model is not loaded. Please ensure models are set up.",
            )

        try:
            # Run inference
            result = self._classifier.predict(image)
            monument_id = result["monument_id"]
            monument_name = result["monument_name"]
            confidence = result["confidence"]
            top_candidates = result.get("top_candidates", [])

            # Check confidence threshold
            if confidence < CONFIDENCE_THRESHOLD:
                suggestions = [c["name"] for c in top_candidates if c.get("name")]
                logger.info(
                    f"Low confidence ({confidence:.2f}) for '{monument_name}' — returning unconfirmed"
                )
                return IdentifyNotRecognizedResponse(
                    confidence=confidence,
                    suggestions=suggestions,
                    message="Monument architectural features unconfirmed or confidence below verification threshold.",
                )

            # Enrich with archival metadata
            meta = self._monument_metadata.get(monument_id, {})
            location = meta.get("location")
            era = meta.get("era")

            logger.info(
                f"Identified '{monument_name}' ({monument_id}) with {confidence*100:.1f}% confidence"
            )

            return IdentifyResponse(
                monument_id=monument_id,
                monument_name=monument_name,
                confidence=confidence,
                location=location,
                era=era,
                recognized=True,
            )

        except Exception as e:
            logger.error(f"Inference error during monument identification: {e}")
            return IdentifyNotRecognizedResponse(
                confidence=0.0,
                suggestions=[],
                message=f"Identification error: {str(e)}",
            )
