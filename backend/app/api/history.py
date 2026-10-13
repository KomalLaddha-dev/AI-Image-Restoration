"""
History API routes — GET /history/{monument_id}
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import HistoryResponse, SourceCitation, TimelineEvent

router = APIRouter(prefix="/api/v1", tags=["Historical Information"])

# In-memory cache for monument metadata
_monument_metadata: dict[str, dict] = {}


def _load_monuments() -> None:
    """Load monument metadata from data/monuments.json."""
    global _monument_metadata
    data_path = Path("data") / "monuments.json"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent.parent / "data" / "monuments.json"
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            monuments = json.load(f)
        _monument_metadata = {m["id"]: m for m in monuments}
        logger.info(f"Loaded {len(_monument_metadata)} monuments from {data_path}")
    else:
        # Use demo data
        _monument_metadata = _get_demo_data()
        logger.info("Using demo monument data")


def _get_demo_data() -> dict[str, dict]:
    """Demo monument metadata for testing."""
    return {
        "taj_mahal": {
            "id": "taj_mahal",
            "name": "Taj Mahal",
            "era": "1632–1653 CE",
            "builder": "Emperor Shah Jahan",
            "architectural_style": "Mughal architecture",
            "unesco_status": "World Heritage Site (1983)",
            "location": "Agra, Uttar Pradesh, India",
            "coordinates": [27.1751, 78.0421],
            "timeline": [
                {"year": "1631", "event": "Mumtaz Mahal dies; Shah Jahan commissions the Taj Mahal as her mausoleum"},
                {"year": "1632", "event": "Construction begins under chief architect Ustad Ahmad Lahori"},
                {"year": "1643", "event": "Main mausoleum structure completed"},
                {"year": "1653", "event": "Entire complex including gardens and mosque completed"},
                {"year": "1983", "event": "Designated a UNESCO World Heritage Site"},
            ],
        },
        "colosseum": {
            "id": "colosseum",
            "name": "Colosseum",
            "era": "70–80 CE",
            "builder": "Emperor Vespasian, completed by Titus",
            "architectural_style": "Roman architecture",
            "unesco_status": "World Heritage Site (1980)",
            "location": "Rome, Italy",
            "coordinates": [41.8902, 12.4922],
            "timeline": [
                {"year": "70 CE", "event": "Construction begins under Emperor Vespasian"},
                {"year": "80 CE", "event": "Inaugurated by Emperor Titus with 100 days of games"},
                {"year": "217 CE", "event": "Damaged by fire caused by lightning"},
                {"year": "1349", "event": "Major earthquake causes south side to collapse"},
                {"year": "1980", "event": "Designated a UNESCO World Heritage Site"},
            ],
        },
        "pyramids_giza": {
            "id": "pyramids_giza",
            "name": "Pyramids of Giza",
            "era": "c. 2580–2560 BCE",
            "builder": "Pharaohs Khufu, Khafre, and Menkaure",
            "architectural_style": "Ancient Egyptian architecture",
            "unesco_status": "World Heritage Site (1979)",
            "location": "Giza, Egypt",
            "coordinates": [29.9792, 31.1342],
            "timeline": [
                {"year": "c. 2580 BCE", "event": "Great Pyramid of Khufu construction begins"},
                {"year": "c. 2560 BCE", "event": "Great Pyramid completed — the tallest man-made structure for 3,800 years"},
                {"year": "c. 2530 BCE", "event": "Pyramid of Khafre and the Great Sphinx constructed"},
                {"year": "1979", "event": "Memphis and its Necropolis designated a UNESCO World Heritage Site"},
            ],
        },
    }


@router.get(
    "/history/{monument_id}",
    response_model=HistoryResponse,
    summary="Get historical information for a monument",
    description="Returns a detailed historical summary, timeline, and source citations "
    "for the specified monument. Summary is generated via RAG (grounded in verified sources).",
)
async def get_monument_history(
    monument_id: str,
    query: str = Query(
        default=None,
        description="Optional focus query, e.g. 'when was it built?' or 'architectural style'",
    ),
):
    """Get historical info for a monument via RAG."""
    # Load metadata if not already loaded
    if not _monument_metadata:
        _load_monuments()

    metadata = _monument_metadata.get(monument_id)
    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail=f"Monument '{monument_id}' not found in database",
        )

    # Try RAG-generated summary
    summary = ""
    sources = []
    try:
        from app.main import get_rag_components
        retriever, generator = get_rag_components()

        if retriever.is_loaded:
            search_query = query or f"history of {metadata['name']}"
            chunks = retriever.search(search_query, monument_id=monument_id, top_k=5)

            if chunks:
                summary = await generator.generate_summary(
                    metadata["name"], chunks, query
                )
                sources = [
                    SourceCitation(name=c.source, url=c.source_url)
                    for c in chunks
                ]
    except Exception as e:
        logger.error(f"RAG generation failed for {monument_id}: {e}")

    # Fallback summary from metadata
    if not summary:
        summary = (
            f"{metadata['name']} is a historic monument located in "
            f"{metadata.get('location', 'an undisclosed location')}. "
            f"It was built during {metadata.get('era', 'an unknown era')}"
            f"{' by ' + metadata['builder'] if metadata.get('builder') else ''}. "
            f"It is recognized as a {metadata.get('architectural_style', 'significant architectural')} landmark."
        )

    # Build timeline
    timeline = [
        TimelineEvent(**event)
        for event in metadata.get("timeline", [])
    ]

    return HistoryResponse(
        monument_id=monument_id,
        name=metadata["name"],
        summary=summary,
        era=metadata.get("era"),
        builder=metadata.get("builder"),
        architectural_style=metadata.get("architectural_style"),
        unesco_status=metadata.get("unesco_status"),
        location=metadata.get("location"),
        coordinates=metadata.get("coordinates"),
        sources=sources,
        timeline=timeline,
    )
