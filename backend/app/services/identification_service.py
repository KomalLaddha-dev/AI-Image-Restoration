"""
Monument identification service — wraps the classifier and
provides fallback handling for unrecognized images.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from loguru import logger

from app.config import get_settings
from app.models.schemas import IdentifyResponse, IdentifyNotRecognizedResponse


# Confidence threshold — below this, return "not recognized"
CONFIDENCE_THRESHOLD = 0.6


class IdentificationService:
    """Identifies monuments from images using the fine-tuned classifier."""

    def __init__(self):
        self._classifier = None
        self._labels: dict[int, dict] = {}
        self._loaded = False

    def load(self) -> None:
        """Load the monument classifier and label mapping."""
        settings = get_settings()
        labels_path = Path(settings.model_dir) / "labels.json"

        if labels_path.exists():
            with open(labels_path) as f:
                self._labels = json.load(f)
            logger.info(f"Loaded {len(self._labels)} monument labels")
        else:
            logger.warning(f"Labels file not found at {labels_path}")
            # Load default demo labels
            self._labels = self._get_demo_labels()

        # TODO: Load ONNX model when trained
        # model_path = Path(settings.model_dir) / "monument_classifier.onnx"
        # if model_path.exists():
        #     import onnxruntime as ort
        #     self._classifier = ort.InferenceSession(str(model_path))
        #     self._loaded = True

        logger.info("Identification service initialized (demo mode)")

    def _get_demo_labels(self) -> dict[str, dict]:
        """Demo label set for testing before the classifier is trained."""
        monuments = [
            {"id": "taj_mahal", "name": "Taj Mahal", "location": "Agra, India", "era": "1632–1653 CE"},
            {"id": "red_fort", "name": "Red Fort", "location": "Delhi, India", "era": "1638–1648 CE"},
            {"id": "qutub_minar", "name": "Qutub Minar", "location": "Delhi, India", "era": "1192–1220 CE"},
            {"id": "india_gate", "name": "India Gate", "location": "Delhi, India", "era": "1921–1931 CE"},
            {"id": "hawa_mahal", "name": "Hawa Mahal", "location": "Jaipur, India", "era": "1799 CE"},
            {"id": "gateway_of_india", "name": "Gateway of India", "location": "Mumbai, India", "era": "1911–1924 CE"},
            {"id": "colosseum", "name": "Colosseum", "location": "Rome, Italy", "era": "70–80 CE"},
            {"id": "eiffel_tower", "name": "Eiffel Tower", "location": "Paris, France", "era": "1887–1889 CE"},
            {"id": "great_wall", "name": "Great Wall of China", "location": "China", "era": "7th century BCE – 1644 CE"},
            {"id": "machu_picchu", "name": "Machu Picchu", "location": "Cusco, Peru", "era": "c. 1450 CE"},
            {"id": "pyramids_giza", "name": "Pyramids of Giza", "location": "Giza, Egypt", "era": "c. 2580–2560 BCE"},
            {"id": "parthenon", "name": "Parthenon", "location": "Athens, Greece", "era": "447–432 BCE"},
            {"id": "angkor_wat", "name": "Angkor Wat", "location": "Siem Reap, Cambodia", "era": "12th century CE"},
            {"id": "statue_of_liberty", "name": "Statue of Liberty", "location": "New York, USA", "era": "1875–1886 CE"},
            {"id": "big_ben", "name": "Big Ben", "location": "London, UK", "era": "1843–1859 CE"},
        ]
        return {str(i): m for i, m in enumerate(monuments)}

    async def identify(
        self, image: np.ndarray
    ) -> IdentifyResponse | IdentifyNotRecognizedResponse:
        """
        Identify a monument from an image.

        Returns IdentifyResponse if confidence >= threshold,
        IdentifyNotRecognizedResponse otherwise.
        """
        if not self._labels:
            self.load()

        # TODO: Run actual classifier inference when model is trained
        # For now, return a demo response to enable end-to-end testing
        if self._classifier is not None:
            return await self._run_classifier(image)

        # Demo mode — return first label with a note
        logger.warning("Classifier not loaded — returning demo identification")
        demo = list(self._labels.values())[0]
        return IdentifyResponse(
            monument_id=demo["id"],
            monument_name=demo["name"],
            confidence=0.0,  # Indicates demo mode
            location=demo.get("location"),
            era=demo.get("era"),
            recognized=True,
        )

    async def _run_classifier(self, image: np.ndarray) -> IdentifyResponse | IdentifyNotRecognizedResponse:
        """Run actual ONNX classifier inference."""
        import cv2
        import onnxruntime as ort

        # Preprocess: resize to 224x224, normalize to ImageNet mean/std
        img_resized = cv2.resize(image, (224, 224))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_float = img_rgb.astype(np.float32) / 255.0

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_normalized = (img_float - mean) / std

        # To NCHW format
        input_tensor = np.expand_dims(img_normalized.transpose(2, 0, 1), axis=0).astype(np.float32)

        # Run inference
        outputs = self._classifier.run(None, {"input": input_tensor})
        logits = outputs[0][0]

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])

        if confidence < CONFIDENCE_THRESHOLD:
            # Get top-3 for suggestions
            top3_idx = np.argsort(probs)[-3:][::-1]
            suggestions = [
                self._labels.get(str(i), {}).get("name", "Unknown")
                for i in top3_idx
            ]
            return IdentifyNotRecognizedResponse(
                confidence=confidence,
                suggestions=suggestions,
                message="This monument is not in our database yet, or confidence is too low.",
            )

        monument = self._labels.get(str(top_idx), {})
        return IdentifyResponse(
            monument_id=monument.get("id", f"monument_{top_idx}"),
            monument_name=monument.get("name", "Unknown Monument"),
            confidence=confidence,
            location=monument.get("location"),
            era=monument.get("era"),
        )
