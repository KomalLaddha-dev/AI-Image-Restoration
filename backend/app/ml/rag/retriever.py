"""
RAG Retriever — FAISS-backed similarity search over historical text chunks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger

from app.ml.rag.embedder import Embedder


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    text: str
    monument_id: str
    source: str
    source_url: str | None = None


class Retriever:
    """FAISS-backed vector retriever over curated historical chunks."""

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self._index = None
        self._chunks: list[Chunk] = []
        self._loaded = False

    def load(self, corpus_dir: str | Path) -> None:
        """
        Build FAISS index from corpus files in the given directory.

        Expected file format per monument (JSON):
        {
            "monument_id": "taj_mahal",
            "chunks": [
                {"text": "...", "source": "Wikipedia", "source_url": "https://..."}
            ]
        }
        """
        corpus_path = Path(corpus_dir)
        if not corpus_path.exists():
            logger.warning(f"Corpus directory not found: {corpus_path}")
            return

        # Load all chunks from corpus files
        all_chunks = []
        for file_path in sorted(corpus_path.glob("*.json")):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                monument_id = data.get("monument_id", file_path.stem)
                for chunk_data in data.get("chunks", []):
                    all_chunks.append(Chunk(
                        text=chunk_data["text"],
                        monument_id=monument_id,
                        source=chunk_data.get("source", "Unknown"),
                        source_url=chunk_data.get("source_url"),
                    ))
            except Exception as e:
                logger.error(f"Failed to load corpus file {file_path}: {e}")

        if not all_chunks:
            logger.warning("No chunks loaded from corpus")
            return

        self._chunks = all_chunks
        logger.info(f"Loaded {len(self._chunks)} chunks from {corpus_path}")

        # Build FAISS index
        self._build_index()

    def _build_index(self) -> None:
        """Embed all chunks and build a FAISS inner-product index."""
        try:
            import faiss
        except ImportError:
            logger.error("faiss-cpu not installed. Retriever unavailable.")
            return

        texts = [c.text for c in self._chunks]
        embeddings = self.embedder.embed(texts)

        # IndexFlatIP = brute-force inner product (fine for < 10K vectors)
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        self._loaded = True
        logger.info(f"Built FAISS index with {self._index.ntotal} vectors (dim={dim})")

    def search(
        self,
        query: str,
        monument_id: str | None = None,
        top_k: int = 5,
    ) -> list[Chunk]:
        """
        Search for the most relevant chunks.

        Args:
            query: Search query text.
            monument_id: If provided, filter results to this monument only.
            top_k: Number of results to return.

        Returns:
            List of matching Chunk objects, sorted by relevance.
        """
        if not self._loaded or self._index is None:
            logger.warning("FAISS index not loaded")
            # Fallback: return chunks for the monument (unranked)
            if monument_id:
                return [c for c in self._chunks if c.monument_id == monument_id][:top_k]
            return []

        query_vec = self.embedder.embed_single(query)
        query_vec = np.expand_dims(query_vec, axis=0)

        # Search more than top_k if filtering by monument_id
        search_k = top_k * 5 if monument_id else top_k
        scores, indices = self._index.search(query_vec, min(search_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = self._chunks[idx]
            if monument_id and chunk.monument_id != monument_id:
                continue
            results.append(chunk)
            if len(results) >= top_k:
                break

        return results

    def get_chunks_for_monument(self, monument_id: str) -> list[Chunk]:
        """Get all chunks for a specific monument (unranked)."""
        return [c for c in self._chunks if c.monument_id == monument_id]

    @property
    def is_loaded(self) -> bool:
        return self._loaded
