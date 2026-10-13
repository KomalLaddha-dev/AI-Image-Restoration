"""
RAG Generator — produces grounded historical summaries using Groq LLM.
NEVER generates answers without retrieved context. All facts must be cited.
"""

from __future__ import annotations

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.ml.rag.retriever import Chunk


class Generator:
    """Groq-powered grounded text generation for historical info."""

    MODEL = "qwen/qwen3.8-27b"
    MAX_TOKENS = 600
    TEMPERATURE = 0.3  # Low for factual accuracy

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-initialize Groq client."""
        if self._client is None:
            settings = get_settings()
            if not settings.groq_api_key:
                logger.error("GROQ_API_KEY not set — RAG generation unavailable")
                return None
            try:
                from groq import Groq
                self._client = Groq(api_key=settings.groq_api_key)
                logger.info("Groq client initialized")
            except ImportError:
                logger.error("groq package not installed")
        return self._client

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=2),
        reraise=False,
    )
    async def generate_summary(
        self,
        monument_name: str,
        chunks: list[Chunk],
        query: str | None = None,
    ) -> str:
        """
        Generate a grounded historical summary from retrieved chunks.

        Args:
            monument_name: Name of the monument.
            chunks: Retrieved text chunks with source citations.
            query: Optional user query to focus the summary.

        Returns:
            A cited historical summary string.
        """
        client = self._get_client()
        if client is None:
            return self._fallback_summary(monument_name, chunks)

        if not chunks:
            return (
                f"No historical information is currently available for {monument_name}. "
                "Please check back later as we expand our knowledge base."
            )

        # Build grounded prompt with strict citation rules
        context = "\n\n".join(
            [f"[{c.source}]: {c.text}" for c in chunks]
        )

        focus = f" Focus on: {query}" if query else ""

        system_prompt = (
            "You are a knowledgeable historian. Your role is to provide accurate, "
            "well-cited historical summaries based ONLY on the provided source material. "
            "You must NEVER invent, assume, or hallucinate any historical facts."
        )

        user_prompt = f"""Write a concise, engaging historical summary about **{monument_name}**.{focus}

## VERIFIED SOURCES:
{context}

## STRICT RULES:
1. Use ONLY information from the sources above — do NOT add any facts not present in these sources.
2. Cite each fact inline using [Source Name] format.
3. If the sources don't contain enough information, explicitly state what is unknown.
4. Organize the summary with: brief intro → key historical facts → significance.
5. Keep the summary between 150–300 words.
6. Use a warm, engaging tone suitable for tourists and students."""

        try:
            response = client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )
            summary = response.choices[0].message.content
            logger.info(f"Generated summary for {monument_name} ({len(summary)} chars)")
            return summary

        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return self._fallback_summary(monument_name, chunks)

    def _fallback_summary(self, monument_name: str, chunks: list[Chunk]) -> str:
        """
        Fallback when LLM is unavailable — concatenate source texts directly.
        Not as polished but preserves accuracy.
        """
        if not chunks:
            return f"Historical information for {monument_name} is being compiled."

        texts = []
        for chunk in chunks[:3]:  # Top 3 chunks
            texts.append(f"{chunk.text} — [{chunk.source}]")

        return f"**{monument_name}**\n\n" + "\n\n".join(texts)
