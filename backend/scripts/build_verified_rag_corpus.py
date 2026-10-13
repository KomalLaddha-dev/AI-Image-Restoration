"""
Build Verified RAG Corpus from Real Wikipedia Pages
===================================================
Fetches real Wikipedia pages for all 12 monuments via HTTP, extracts
concise factual paragraphs, sets source_url to the exact fetched URL,
adds 'source': 'Wikipedia (CC BY-SA)', and flags 'verified': True.
Also performs a spot-check of 10 random chunks against their URLs.
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "HeritageRestore/1.0 (historical-rag-corpus@heritagerestore.org)"
}

MONUMENTS_TARGETS = [
    {
        "id": "taj_mahal",
        "name": "Taj Mahal",
        "wiki_title": "Taj Mahal",
    },
    {
        "id": "red_fort",
        "name": "Red Fort",
        "wiki_title": "Red Fort",
    },
    {
        "id": "qutub_minar",
        "name": "Qutub Minar",
        "wiki_title": "Qutb Minar",
    },
    {
        "id": "colosseum",
        "name": "Colosseum",
        "wiki_title": "Colosseum",
    },
    {
        "id": "eiffel_tower",
        "name": "Eiffel Tower",
        "wiki_title": "Eiffel Tower",
    },
    {
        "id": "pyramids_giza",
        "name": "Pyramids of Giza",
        "wiki_title": "Giza pyramid complex",
    },
    {
        "id": "machu_picchu",
        "name": "Machu Picchu",
        "wiki_title": "Machu Picchu",
    },
    {
        "id": "hawa_mahal",
        "name": "Hawa Mahal",
        "wiki_title": "Hawa Mahal",
    },
    {
        "id": "angkor_wat",
        "name": "Angkor Wat",
        "wiki_title": "Angkor Wat",
    },
    {
        "id": "gateway_of_india",
        "name": "Gateway of India",
        "wiki_title": "Gateway of India",
    },
    {
        "id": "parthenon",
        "name": "Parthenon",
        "wiki_title": "Parthenon",
    },
    {
        "id": "statue_of_liberty",
        "name": "Statue of Liberty",
        "wiki_title": "Statue of Liberty",
    },
]


def fetch_wikipedia_content(title: str) -> tuple[str, str, int]:
    """
    Fetch plain-text extracted content from Wikipedia API.
    Returns (clean_text, exact_url, http_status).
    """
    encoded_title = urllib.parse.quote(title.replace(" ", "_"))
    api_url = (
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
        f"&explaintext=1&titles={encoded_title}"
    )
    exact_page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"

    req = urllib.request.Request(api_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            return extract, exact_page_url, status

    raise ValueError(f"No content found for title {title}")


def clean_and_chunk_text(full_text: str, max_chunks: int = 5) -> list[str]:
    """
    Splits Wikipedia extract into clean paragraphs, filters out short/navigational
    lines, and selects key factual sections.
    """
    paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
    candidate_chunks: list[str] = []

    for para in paragraphs:
        # Skip section headings (e.g. '== History ==')
        if para.startswith("=") and para.endswith("="):
            continue
        # Skip very short fragments
        if len(para.split()) < 30:
            continue
        # Remove footnote markers like [1], [2] if any
        cleaned = re.sub(r"\[\d+\]", "", para).strip()
        candidate_chunks.append(cleaned)

    # Pick up to max_chunks (e.g. Lead, History, Architecture, Cultural Significance)
    selected = candidate_chunks[:max_chunks]
    return selected


def build_corpus():
    base_dir = Path(__file__).resolve().parent.parent
    corpus_dir = base_dir / "data" / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    all_verified_chunks: list[dict[str, Any]] = []

    print("\n" + "=" * 80)
    print("FETCHING REAL PAGES & BUILDING VERIFIED RAG CORPUS")
    print("=" * 80)

    for item in MONUMENTS_TARGETS:
        m_id = item["id"]
        m_name = item["name"]
        wiki_title = item["wiki_title"]

        try:
            logger.info(f"Fetching Wikipedia page for '{wiki_title}'...")
            extract, page_url, status = fetch_wikipedia_content(wiki_title)
            chunks_text = clean_and_chunk_text(extract, max_chunks=5)

            chunks_data = []
            for c_text in chunks_text:
                chunk_obj = {
                    "text": c_text,
                    "source": "Wikipedia (CC BY-SA)",
                    "source_url": page_url,
                    "verified": True,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
                chunks_data.append(chunk_obj)
                all_verified_chunks.append({
                    "monument_id": m_id,
                    "monument_name": m_name,
                    **chunk_obj,
                })

            # For taj_mahal, let's also append an unverified dummy chunk to test retriever exclusion
            if m_id == "taj_mahal":
                unverified_chunk = {
                    "text": "Unverified rumor: An entire secondary black marble mausoleum was fully built across the river.",
                    "source": "Unverified Folk Tale",
                    "source_url": None,
                    "verified": False,
                    "fetched_at": None,
                }
                chunks_data.append(unverified_chunk)

            monument_corpus = {
                "monument_id": m_id,
                "name": m_name,
                "chunks": chunks_data,
            }

            dest_file = corpus_dir / f"{m_id}.json"
            dest_file.write_text(json.dumps(monument_corpus, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(
                f"Saved {len(chunks_data)} chunks for {m_name} to {dest_file.name} "
                f"(Status={status}, URL={page_url})"
            )
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Failed to fetch {m_name}: {e}")

    print("\n" + "=" * 80)
    print(f"CORPUS GENERATION COMPLETE: {len(all_verified_chunks)} VERIFIED CHUNKS CREATED")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────────
    # SPOT-CHECK 10 RANDOM CHUNKS AGAINST THEIR REAL SOURCE URLS
    # ─────────────────────────────────────────────────────────────────────────────
    spot_check_chunks(all_verified_chunks, k=10)


def spot_check_chunks(chunks: list[dict[str, Any]], k: int = 10):
    print("\n" + "=" * 90)
    print(f"SPOT-CHECKING {k} RANDOM CHUNKS AGAINST LIVE SOURCE URLS")
    print("=" * 90)

    random.seed(42)
    sample_chunks = random.sample(chunks, min(k, len(chunks)))

    results = []

    for idx, c in enumerate(sample_chunks, start=1):
        url = c["source_url"]
        m_name = c["monument_name"]
        text = c["text"]

        # Pick 2-3 salient words/phrases from text (length > 5)
        words = [w.lower().strip(".,;:\"'()[]") for w in text.split() if len(w) > 5]
        test_keywords = words[:3]

        # Fetch the live page directly
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8", errors="ignore").lower()

                matches = [kw for kw in test_keywords if kw in body]
                is_match = len(matches) >= 2

                results.append({
                    "idx": idx,
                    "monument": m_name,
                    "url": url,
                    "status": status_code,
                    "keywords": test_keywords,
                    "matched": matches,
                    "verified": c["verified"] and (status_code == 200) and is_match,
                })
        except Exception as e:
            results.append({
                "idx": idx,
                "monument": m_name,
                "url": url,
                "status": str(e),
                "keywords": test_keywords,
                "matched": [],
                "verified": False,
            })

    print(f"{'#':<3} | {'Monument':<18} | {'Status':<6} | {'Matched Keywords':<26} | {'Verified'}")
    print("-" * 90)
    for r in results:
        status_str = f"HTTP {r['status']}" if isinstance(r['status'], int) else "FAIL"
        matched_str = ", ".join(r['matched']).encode("ascii", "ignore").decode("ascii")
        ver_str = "PASSED (CC BY-SA)" if r['verified'] else "FAILED"
        print(f"{r['idx']:<3} | {r['monument']:<18} | {status_str:<6} | {matched_str:<26} | {ver_str}")

    print("=" * 90 + "\n")


if __name__ == "__main__":
    build_corpus()
