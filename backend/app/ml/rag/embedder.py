"""
RAG Embedder — generates sentence embeddings using all-MiniLM-L6-v2.
Embeds text chunks for the FAISS vector store.
"""

from __future__ import annotations

import numpy as np
from loguru import logger


class Embedder:
    """Sentence embedding using all-MiniLM-L6-v2 (384-dim)."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(self):
        self._model = None

    def load(self) -> None:
        """Lazy-load the sentence transformer model."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.MODEL_NAME)
            logger.info(f"Loaded embedding model: {self.MODEL_NAME}")
        except ImportError:
            logger.error("sentence-transformers not installed. RAG embedding unavailable.")

    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Embed a list of texts into normalized vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            NumPy array of shape (len(texts), 384).
        """
        if self._model is None:
            self.load()
        if self._model is None:
            raise RuntimeError("Embedding model not loaded")

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,  # L2-normalize for cosine similarity
            show_progress_bar=False,
            batch_size=32,
        )
        return np.array(embeddings, dtype=np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self.embed([text])[0]
