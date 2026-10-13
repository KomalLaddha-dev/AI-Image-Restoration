"""
Tests for Verified RAG Corpus, Retriever & Grounded History (Phase 2)
=====================================================================
Validates:
- All corpus files in data/corpus/ contain verified chunks with source URLs and CC BY-SA.
- Retriever strictly excludes unverified chunks ("verified": False).
- FAISS vector search retrieves relevant verified chunks for queries.
- Fallback generation cleanly produces grounded text with source attribution.
- FastAPI endpoint GET /api/v1/history/{monument_id} returns 200 with structured facts and citations.
- 404 handling for unknown monument IDs.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.rag.embedder import Embedder
from app.ml.rag.retriever import Retriever, Chunk
from app.ml.rag.generator import Generator
from app.models.schemas import HistoryResponse

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "corpus"


@pytest.fixture
def embedder():
    emb = Embedder()
    emb.load()
    return emb


@pytest.fixture
def retriever(embedder):
    ret = Retriever(embedder)
    ret.load(CORPUS_DIR)
    return ret


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


def test_corpus_files_exist_and_verified():
    """Ensure all 12 monuments have verified corpus files with CC BY-SA attribution."""
    assert CORPUS_DIR.exists(), f"Corpus dir not found: {CORPUS_DIR}"
    corpus_files = list(CORPUS_DIR.glob("*.json"))
    assert len(corpus_files) >= 12, f"Expected at least 12 corpus files, found {len(corpus_files)}"

    total_chunks = 0
    verified_chunks = 0
    for f in corpus_files:
        import json
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        chunks = data.get("chunks", [])
        assert len(chunks) > 0, f"No chunks in {f.name}"
        for c in chunks:
            total_chunks += 1
            if c.get("verified", True):
                verified_chunks += 1
                assert "source_url" in c and c["source_url"].startswith("https://")
                assert "CC BY-SA" in c["source"] or "UNESCO" in c["source"] or "Wikipedia" in c["source"]

    assert verified_chunks >= 60, f"Expected >= 60 verified chunks, found {verified_chunks}"


def test_retriever_excludes_unverified_chunks(retriever):
    """Ensure retriever strictly excludes any chunk with verified=False."""
    assert retriever.is_loaded is True

    # Search specifically for the unverified black marble rumor
    results = retriever.search("black marble mausoleum river", monument_id="taj_mahal", top_k=5)
    for c in results:
        assert "Unverified rumor" not in c.text
        assert c.verified is True


def test_retriever_search_precision(retriever):
    """Test retrieval for specific monuments and queries."""
    # 1. Taj Mahal
    taj_chunks = retriever.search("Shah Jahan Mumtaz Mahal marble", monument_id="taj_mahal", top_k=3)
    assert len(taj_chunks) > 0
    assert any("Shah Jahan" in c.text or "Taj Mahal" in c.text for c in taj_chunks)
    assert taj_chunks[0].source_url.startswith("https://en.wikipedia.org/wiki/Taj_Mahal")

    # 2. Colosseum
    colo_chunks = retriever.search("Flavian amphitheatre Roman gladiators", monument_id="colosseum", top_k=3)
    assert len(colo_chunks) > 0
    assert any("Colosseum" in c.text or "amphitheatre" in c.text or "Rome" in c.text for c in colo_chunks)

    # 3. Pyramids of Giza
    pyramid_chunks = retriever.search("Khufu Pharaoh Great Pyramid", monument_id="pyramids_giza", top_k=3)
    assert len(pyramid_chunks) > 0
    assert any("Pyramid" in c.text or "Giza" in c.text or "Khufu" in c.text for c in pyramid_chunks)


def test_generator_fallback():
    """Test that generator produces cited fallback when Groq client is None."""
    gen = Generator()
    test_chunks = [
        Chunk(
            text="The Taj Mahal is an ivory-white marble mausoleum in Agra.",
            monument_id="taj_mahal",
            source="Wikipedia (CC BY-SA)",
            source_url="https://en.wikipedia.org/wiki/Taj_Mahal",
            verified=True,
        )
    ]
    summary = gen._fallback_summary("Taj Mahal", test_chunks)
    assert "Taj Mahal" in summary
    assert "Wikipedia (CC BY-SA)" in summary
    assert "ivory-white marble" in summary


def test_api_history_endpoint_taj_mahal(client):
    """Test GET /api/v1/history/taj_mahal returns complete verified history."""
    response = client.get("/api/v1/history/taj_mahal")
    assert response.status_code == 200
    data = response.json()

    assert data["monument_id"] == "taj_mahal"
    assert data["name"] == "Taj Mahal"
    assert len(data["summary"]) > 50
    assert len(data["timeline"]) >= 5
    assert len(data["sources"]) > 0
    assert any("wikipedia.org" in s["url"] for s in data["sources"])
    assert data["era"] == "1632–1653 CE"
    assert data["builder"] == "Emperor Shah Jahan"


def test_api_history_endpoint_all_monuments(client, monkeypatch):
    """Test GET /api/v1/history/{monument_id} for all 12 monuments with verified citations."""
    from app.ml.rag.generator import Generator

    async def mock_generate(self, monument_name, chunks, query=None):
        return f"Verified historical profile for {monument_name}."

    monkeypatch.setattr(Generator, "generate_summary", mock_generate)

    monuments = [
        "taj_mahal", "red_fort", "qutub_minar", "colosseum",
        "eiffel_tower", "pyramids_giza", "machu_picchu", "hawa_mahal",
        "angkor_wat", "gateway_of_india", "parthenon", "statue_of_liberty",
    ]
    for m_id in monuments:
        response = client.get(f"/api/v1/history/{m_id}")
        assert response.status_code == 200, f"Failed for monument: {m_id}"
        data = response.json()
        assert data["monument_id"] == m_id
        assert len(data["summary"]) > 0
        assert len(data["sources"]) > 0
        assert any("wikipedia.org" in s["url"] for s in data["sources"])


def test_groq_api_key_absent_fallback(client, monkeypatch):
    """Test that when GROQ_API_KEY is absent, system falls back cleanly to verified facts."""
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", None)

    from app.main import get_rag_components
    _, gen = get_rag_components()
    monkeypatch.setattr(gen, "_client", None)

    response = client.get("/api/v1/history/taj_mahal")
    assert response.status_code == 200
    data = response.json()
    assert data["monument_id"] == "taj_mahal"
    assert len(data["summary"]) > 0
    assert len(data["sources"]) > 0
    assert data["builder"] == "Emperor Shah Jahan"


def test_api_history_endpoint_not_found(client):
    """Test GET /api/v1/history/{monument_id} returns 404 for unknown monument."""
    response = client.get("/api/v1/history/unknown_monument_xyz")
    assert response.status_code == 404
