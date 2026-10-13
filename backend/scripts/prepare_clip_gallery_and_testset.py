"""
Prepare CLIP Reference Gallery & Held-Out Test Set
==================================================
Builds:
1. Reference Gallery: 2-3 canonical photos per monument in backend/data/reference_gallery/
2. Held-Out Test Set:
   - In-gallery: 5 photos per monument in backend/data/test_set/in_gallery/ (includes degraded/sepia)
   - Unseen monuments: 5 landmarks not in the gallery in backend/data/test_set/unseen_monuments/
   - Non-monuments: 10 images (nature, people, vehicles, interiors) in backend/data/test_set/non_monuments/
3. Precomputes and saves CLIP reference gallery embeddings to backend/data/gallery_embeddings.pt
Strictly enforces: gallery images are NEVER in the test set.
"""

import hashlib
import json
import time
import urllib.parse
import urllib.request
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image
from sentence_transformers import SentenceTransformer

from app.eval.degrade import apply_sepia, add_noise, add_scratches, add_blur

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GALLERY_DIR = DATA_DIR / "reference_gallery"
TEST_DIR = DATA_DIR / "test_set"

HEADERS = {"User-Agent": "HeritageRestore/1.0 (academic-cv-research)"}


def compute_file_hash(path: Path) -> str:
    """Compute MD5 hash of an image file to guarantee disjoint sets."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def search_commons(query: str, limit: int = 15) -> list[str]:
    """Search Wikimedia Commons for images."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 600,
        "format": "json",
    }
    url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        urls = []
        for p in pages.values():
            infos = p.get("imageinfo", [])
            if infos and "thumburl" in infos[0]:
                u = infos[0]["thumburl"]
                if any(ext in u.lower() for ext in [".jpg", ".jpeg", ".png"]):
                    urls.append(u)
        return urls
    except Exception as e:
        logger.warning(f"Failed to search Wikimedia for '{query}': {e}")
        return []


def download_image(url: str, dest: Path) -> bool:
    """Download image from URL and verify it can be parsed by PIL."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        dest.write_bytes(data)
        # Verify valid image
        with Image.open(dest) as img:
            img.verify()
        return True
    except Exception as e:
        if dest.exists():
            dest.unlink(missing_ok=True)
        return False


def main():
    logger.info("Initializing Reference Gallery and Held-Out Test Set creation...")
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    monuments_file = DATA_DIR / "monuments.json"
    with open(monuments_file, encoding="utf-8") as f:
        monuments: list[dict] = json.load(f)

    gallery_hashes = set()
    test_hashes = set()

    # ─────────────────────────────────────────────────────────────────────────────
    # 1. Download Gallery and Test Images for In-Gallery Monuments
    # ─────────────────────────────────────────────────────────────────────────────
    for m in monuments:
        m_id = m["id"]
        m_name = m["name"]
        logger.info(f"Processing in-gallery monument: {m_name} ({m_id})")

        m_gallery_dir = GALLERY_DIR / m_id
        m_test_dir = TEST_DIR / "in_gallery" / m_id
        m_gallery_dir.mkdir(parents=True, exist_ok=True)
        m_test_dir.mkdir(parents=True, exist_ok=True)

        # Search Wikimedia Commons
        urls = search_commons(m_name, limit=20)
        logger.info(f"Found {len(urls)} candidate URLs for {m_name}")

        downloaded_paths = []
        for idx, u in enumerate(urls):
            temp_path = m_gallery_dir / f"temp_{idx}.jpg"
            if download_image(u, temp_path):
                downloaded_paths.append(temp_path)
            if len(downloaded_paths) >= 8:
                break

        if len(downloaded_paths) < 6:
            logger.warning(f"Only {len(downloaded_paths)} images found for {m_name}")

        # Split: First 2 for Reference Gallery, Remaining for Test Set
        # Gallery
        for g_idx in range(min(2, len(downloaded_paths))):
            p = downloaded_paths[g_idx]
            final_p = m_gallery_dir / f"ref_{g_idx + 1}.jpg"
            p.rename(final_p)
            gallery_hashes.add(compute_file_hash(final_p))

        # Held-out Test Set (clean)
        test_images_assigned = 0
        for t_idx in range(2, min(5, len(downloaded_paths))):
            p = downloaded_paths[t_idx]
            final_p = m_test_dir / f"test_clean_{test_images_assigned + 1}.jpg"
            p.rename(final_p)
            test_hashes.add(compute_file_hash(final_p))
            test_images_assigned += 1

        # Clean up any leftover temp files
        for extra in downloaded_paths[5:]:
            if extra.exists():
                extra.unlink()

        # Held-out Test Set (degraded / sepia photos)
        # Synthesize 2 degraded variations from the test clean images
        clean_tests = list(m_test_dir.glob("test_clean_*.jpg"))
        if clean_tests:
            # Degraded 1: Sepia + scratches
            base_img = cv2.imread(str(clean_tests[0]))
            deg1 = apply_sepia(base_img)
            deg1 = add_scratches(deg1, num_scratches=12)
            deg1_path = m_test_dir / "test_degraded_sepia_scratches.jpg"
            cv2.imwrite(str(deg1_path), deg1)
            test_hashes.add(compute_file_hash(deg1_path))

            # Degraded 2: Blur + salt-and-pepper noise
            src = clean_tests[-1] if len(clean_tests) > 1 else clean_tests[0]
            base_img2 = cv2.imread(str(src))
            deg2 = add_noise(base_img2, severity=0.03)
            deg2 = add_blur(deg2, ksize=5)
            deg2_path = m_test_dir / "test_degraded_blur_noise.jpg"
            cv2.imwrite(str(deg2_path), deg2)
            test_hashes.add(compute_file_hash(deg2_path))

    # ─────────────────────────────────────────────────────────────────────────────
    # 2. Download Held-Out Unseen Monuments (Not in Gallery)
    # ─────────────────────────────────────────────────────────────────────────────
    unseen_landmarks = [
        ("big_ben", "Big Ben London"),
        ("stonehenge", "Stonehenge England"),
        ("leaning_tower_pisa", "Leaning Tower of Pisa"),
        ("sydney_opera_house", "Sydney Opera House"),
        ("golden_gate_bridge", "Golden Gate Bridge San Francisco"),
    ]
    unseen_dir = TEST_DIR / "unseen_monuments"
    unseen_dir.mkdir(parents=True, exist_ok=True)

    for u_id, u_query in unseen_landmarks:
        u_landmark_dir = unseen_dir / u_id
        u_landmark_dir.mkdir(parents=True, exist_ok=True)
        urls = search_commons(u_query, limit=10)
        saved = 0
        for idx, u in enumerate(urls):
            target = u_landmark_dir / f"test_{saved + 1}.jpg"
            if download_image(u, target):
                test_hashes.add(compute_file_hash(target))
                saved += 1
            if saved >= 2:
                break
        logger.info(f"Unseen landmark '{u_id}': saved {saved} test images")

    # ─────────────────────────────────────────────────────────────────────────────
    # 3. Download Non-Monument Images
    # ─────────────────────────────────────────────────────────────────────────────
    non_monument_queries = [
        "domestic cat",
        "red sports car",
        "modern bicycle",
        "bowl of fresh fruit",
        "modern office desk",
        "ocean breaking wave",
        "portrait of smiling woman",
        "steam locomotive train",
        "golden retriever dog",
        "living room armchair",
    ]
    non_mon_dir = TEST_DIR / "non_monuments"
    non_mon_dir.mkdir(parents=True, exist_ok=True)

    # Include Detroit 1915 sample
    detroit_src = BASE_DIR.parent / "web-demo" / "public" / "samples" / "detroit_1915.jpg"
    if detroit_src.exists():
        detroit_dest = non_mon_dir / "detroit_1915.jpg"
        detroit_dest.write_bytes(detroit_src.read_bytes())
        test_hashes.add(compute_file_hash(detroit_dest))

    for idx, q in enumerate(non_monument_queries):
        urls = search_commons(q, limit=6)
        target = non_mon_dir / f"non_monument_{idx + 1}.jpg"
        for u in urls:
            if download_image(u, target):
                test_hashes.add(compute_file_hash(target))
                break

    # ─────────────────────────────────────────────────────────────────────────────
    # 4. Strict Disjoint Check
    # ─────────────────────────────────────────────────────────────────────────────
    intersection = gallery_hashes.intersection(test_hashes)
    assert len(intersection) == 0, f"FATAL: Gallery and Test Set overlap on {len(intersection)} image(s)!"
    logger.info(f"Verified disjoint sets: {len(gallery_hashes)} gallery images, {len(test_hashes)} test images. Zero overlap.")

    # ─────────────────────────────────────────────────────────────────────────────
    # 5. Precompute & Persist CLIP Gallery Embeddings
    # ─────────────────────────────────────────────────────────────────────────────
    logger.info("Computing CLIP (clip-ViT-B-32) gallery embeddings...")
    clip_model = SentenceTransformer("clip-ViT-B-32")

    gallery_records = []
    gallery_tensors = []

    for m in monuments:
        m_id = m["id"]
        m_name = m["name"]
        m_gallery_dir = GALLERY_DIR / m_id
        ref_images = sorted(list(m_gallery_dir.glob("ref_*.jpg")))

        for r_path in ref_images:
            try:
                pil_img = Image.open(r_path).convert("RGB")
                emb = clip_model.encode(pil_img, normalize_embeddings=True)  # (512,)
                gallery_tensors.append(torch.tensor(emb, dtype=torch.float32))
                gallery_records.append({
                    "monument_id": m_id,
                    "monument_name": m_name,
                    "file_path": str(r_path.relative_to(DATA_DIR)),
                })
            except Exception as e:
                logger.error(f"Error encoding gallery item {r_path}: {e}")

    gallery_matrix = torch.stack(gallery_tensors, dim=0)  # (N_gallery, 512)
    torch.save(gallery_matrix, DATA_DIR / "gallery_embeddings.pt")

    with open(DATA_DIR / "gallery_meta.json", "w", encoding="utf-8") as f:
        json.dump(gallery_records, f, indent=2)

    logger.info(f"Saved gallery matrix of shape {gallery_matrix.shape} to {DATA_DIR / 'gallery_embeddings.pt'}")
    logger.info(f"Saved gallery metadata ({len(gallery_records)} items) to {DATA_DIR / 'gallery_meta.json'}")
    logger.info("Dataset preparation complete!")


if __name__ == "__main__":
    main()
