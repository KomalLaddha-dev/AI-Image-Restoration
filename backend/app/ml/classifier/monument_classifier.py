"""
Monument Classifier Engine
==========================
Primary visual recognition engine using CLIP (clip-ViT-B-32) + Reference Gallery.
Features:
- Zero-shot visual representation with OpenAI's clip-ViT-B-32 via SentenceTransformers.
- Precomputed reference gallery embeddings across verified monuments.
- Max-pooled cosine similarity per architectural monument class.
- Temperature-scaled softmax confidence calibration.
- Full compatibility with historical and degraded archival photographs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class MonumentClassifier:
    """Production CLIP-based classifier for monuments and heritage landmarks."""

    def __init__(
        self,
        data_dir: Path | str | None = None,
        model_name: str = "clip-ViT-B-32",
        temperature: float = 0.03,
    ):
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).resolve().parent.parent.parent.parent / "data"
        )
        self.model_name = model_name
        self.temperature = temperature

        self.gallery_emb_path = self.data_dir / "gallery_embeddings.pt"
        self.gallery_meta_path = self.data_dir / "gallery_meta.json"

        self.model: SentenceTransformer | None = None
        self.gallery_embeddings: torch.Tensor | None = None
        self.gallery_meta: list[dict[str, Any]] = []
        self.classes: list[str] = []
        self.class_names: dict[str, str] = {}
        self.is_loaded = False

    def load(self) -> bool:
        """Load the CLIP model and reference gallery embeddings."""
        if not self.gallery_emb_path.exists() or not self.gallery_meta_path.exists():
            logger.warning(
                f"Reference gallery artifacts not found at {self.gallery_emb_path} or {self.gallery_meta_path}"
            )
            return False

        if SentenceTransformer is None:
            logger.error("sentence_transformers is not installed")
            return False

        try:
            logger.info(f"Loading CLIP visual encoder: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

            raw_emb = torch.load(self.gallery_emb_path, map_location="cpu")
            # Normalize gallery embeddings for cosine similarity
            self.gallery_embeddings = raw_emb / raw_emb.norm(dim=1, keepdim=True)

            with open(self.gallery_meta_path, encoding="utf-8") as f:
                self.gallery_meta = json.load(f)

            # Build class index mapping
            self.class_names = {}
            for item in self.gallery_meta:
                m_id = item["monument_id"]
                m_name = item["monument_name"]
                self.class_names[m_id] = m_name

            self.classes = sorted(list(self.class_names.keys()))
            self.is_loaded = True
            logger.info(
                f"Loaded MonumentClassifier CLIP engine with {len(self.gallery_meta)} "
                f"reference gallery items across {len(self.classes)} classes."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load CLIP classifier engine: {e}")
            return False

    def preprocess(self, image: np.ndarray | Image.Image) -> Image.Image:
        """Convert input array or image to RGB PIL image for CLIP encoding."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")

        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                img_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                img_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
            else:
                img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(img_rgb)

        raise ValueError(f"Unsupported image type: {type(image)}")

    def predict(
        self,
        image: np.ndarray | Image.Image,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """
        Run inference on an input image.
        Returns:
            dict containing monument_id, monument_name, confidence, raw_similarity, and top_candidates.
        """
        if not self.is_loaded or self.model is None or self.gallery_embeddings is None:
            success = self.load()
            if not success:
                raise RuntimeError("MonumentClassifier failed to load CLIP weights or gallery embeddings.")

        temp = temperature if temperature is not None else self.temperature
        pil_img = self.preprocess(image)

        # Compute normalized image embedding (shape: [512])
        query_emb = self.model.encode(
            pil_img,
            convert_to_tensor=True,
            normalize_embeddings=True,
        ).cpu()

        # Compute cosine similarities against all gallery embeddings (shape: [N_gallery])
        sims = (
            torch.matmul(self.gallery_embeddings, query_emb.unsqueeze(1))
            .squeeze(1)
            .numpy()
        )

        # Max-pool similarities per monument class
        class_sims: dict[str, float] = {c: -1.0 for c in self.classes}
        for idx, item in enumerate(self.gallery_meta):
            m_id = item["monument_id"]
            if sims[idx] > class_sims[m_id]:
                class_sims[m_id] = float(sims[idx])

        scores = np.array([class_sims[c] for c in self.classes], dtype=np.float32)

        # Temperature-scaled softmax
        logits = scores / temp
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        sorted_indices = np.argsort(probs)[::-1]
        top_idx = int(sorted_indices[0])
        top_id = self.classes[top_idx]
        top_name = self.class_names[top_id]
        top_prob = float(probs[top_idx])
        top_sim = float(scores[top_idx])

        # Top candidates
        top_candidates = []
        for idx in sorted_indices[:3]:
            cid = self.classes[idx]
            top_candidates.append({
                "id": cid,
                "name": self.class_names.get(cid, cid),
                "confidence": float(probs[idx]),
                "similarity": float(scores[idx]),
            })

        return {
            "monument_id": top_id,
            "monument_name": top_name,
            "confidence": top_prob,
            "raw_similarity": top_sim,
            "top_candidates": top_candidates,
        }
