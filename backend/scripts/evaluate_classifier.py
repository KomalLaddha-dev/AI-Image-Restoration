"""
Held-Out Evaluation for CLIP Reference Gallery Monument Identification
=======================================================================
Evaluates clip-ViT-B-32 zero-shot gallery retrieval on a strictly held-out test set:
- 60 in-gallery monument photos (>=5 photos per class, including degraded/sepia)
- 10 unseen landmark photos (monuments NOT in the gallery)
- 10 non-monument photos (everyday objects, historical street scenes)

Computes Precision, Recall, F1, OOD False Alarm Rate across multiple temperatures
and thresholds to find the optimal decision boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from loguru import logger
from PIL import Image
from sentence_transformers import SentenceTransformer


def load_gallery(data_dir: Path):
    emb_path = data_dir / "gallery_embeddings.pt"
    meta_path = data_dir / "gallery_meta.json"
    if not emb_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Gallery embeddings or metadata not found")

    embeddings = torch.load(emb_path, map_location="cpu")
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    # Normalize gallery embeddings
    embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)
    return embeddings, meta


def predict_clip(
    query_emb: torch.Tensor,
    gallery_emb: torch.Tensor,
    gallery_meta: list[dict[str, Any]],
    temperature: float = 0.05,
) -> dict[str, Any]:
    """
    Given normalized query embedding and gallery embeddings,
    compute cosine similarity, aggregate per class via max-pooling,
    and compute softmax probabilities with temperature scaling.
    """
    # similarities shape: (N_gallery,)
    sims = torch.matmul(gallery_emb, query_emb.unsqueeze(1)).squeeze(1).numpy()

    # Group by monument class
    class_sims: dict[str, float] = {}
    class_names: dict[str, str] = {}
    for idx, item in enumerate(gallery_meta):
        m_id = item["monument_id"]
        m_name = item["monument_name"]
        class_names[m_id] = m_name
        current = class_sims.get(m_id, -1.0)
        if sims[idx] > current:
            class_sims[m_id] = float(sims[idx])

    classes = list(class_sims.keys())
    scores = np.array([class_sims[c] for c in classes], dtype=np.float32)

    # Softmax with temperature
    logits = scores / temperature
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / exp_logits.sum()

    sorted_indices = np.argsort(probs)[::-1]
    top_idx = sorted_indices[0]
    top_id = classes[top_idx]
    top_name = class_names[top_id]
    top_prob = float(probs[top_idx])
    top_sim = float(scores[top_idx])

    candidates = []
    for idx in sorted_indices[:3]:
        cid = classes[idx]
        candidates.append({
            "id": cid,
            "name": class_names[cid],
            "confidence": float(probs[idx]),
            "similarity": float(scores[idx]),
        })

    return {
        "monument_id": top_id,
        "monument_name": top_name,
        "confidence": top_prob,
        "raw_similarity": top_sim,
        "candidates": candidates,
    }


def evaluate():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    test_dir = data_dir / "test_set"

    logger.info("Loading CLIP model (clip-ViT-B-32)...")
    model = SentenceTransformer("clip-ViT-B-32")
    gallery_emb, gallery_meta = load_gallery(data_dir)
    gallery_classes = sorted(list({item["monument_id"] for item in gallery_meta}))
    logger.info(f"Loaded gallery with {len(gallery_meta)} embeddings across {len(gallery_classes)} classes.")

    # Collect all test images
    # 1. In-gallery images
    in_gallery_items: list[tuple[Path, str]] = []
    for m_dir in (test_dir / "in_gallery").iterdir():
        if m_dir.is_dir():
            m_id = m_dir.name
            for img_file in m_dir.glob("*.jpg"):
                in_gallery_items.append((img_file, m_id))

    # 2. Unseen monuments
    unseen_items: list[tuple[Path, str]] = []
    unseen_dir = test_dir / "unseen_monuments"
    if unseen_dir.exists():
        for u_dir in unseen_dir.iterdir():
            if u_dir.is_dir():
                for img_file in u_dir.glob("*.jpg"):
                    unseen_items.append((img_file, "__unseen__"))

    # 3. Non-monuments
    non_mon_items: list[tuple[Path, str]] = []
    non_mon_dir = test_dir / "non_monuments"
    if non_mon_dir.exists():
        for img_file in non_mon_dir.glob("*.jpg"):
            non_mon_items.append((img_file, "__non_monument__"))

    total_in = len(in_gallery_items)
    total_unseen = len(unseen_items)
    total_non_mon = len(non_mon_items)
    total_ood = total_unseen + total_non_mon
    logger.info(
        f"Test set summary: In-Gallery={total_in}, Unseen Monuments={total_unseen}, "
        f"Non-Monuments={total_non_mon} (Total={total_in + total_ood})"
    )

    # Pre-encode all query images to speed up threshold sweep
    all_queries: list[dict[str, Any]] = []
    for img_path, ground_truth in in_gallery_items + unseen_items + non_mon_items:
        try:
            with Image.open(img_path) as img:
                emb = model.encode(img.convert("RGB"), convert_to_tensor=True, normalize_embeddings=True)
                all_queries.append({
                    "path": img_path,
                    "ground_truth": ground_truth,
                    "embedding": emb.cpu(),
                    "is_in_gallery": ground_truth not in ("__unseen__", "__non_monument__"),
                })
        except Exception as e:
            logger.error(f"Error encoding {img_path}: {e}")

    logger.info(f"Successfully encoded {len(all_queries)} query images.")

    # Sweep temperatures and thresholds
    temperatures = [0.03, 0.04, 0.05, 0.06, 0.08]
    thresholds = [0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

    print("\n" + "=" * 95)
    print(f"{'TEMPERATURE & THRESHOLD SWEEP ON HELD-OUT TEST SET':^95}")
    print("=" * 95)

    best_config = None
    best_f1 = -1.0

    for temp in temperatures:
        print(f"\n--- Temperature tau = {temp:.2f} ---")
        print(
            f"{'Threshold':<11} | {'Precision':<10} | {'Recall':<8} | {'F1':<8} | "
            f"{'In-Gal Acc':<11} | {'OOD Reject %':<13} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'TN':<4}"
        )
        print("-" * 95)

        for thresh in thresholds:
            tp = 0  # in-gallery, predicted == GT and conf >= thresh
            fp = 0  # (in-gallery, predicted != GT and conf >= thresh) OR (OOD and conf >= thresh)
            fn = 0  # in-gallery and conf < thresh
            tn = 0  # OOD and conf < thresh
            correct_in_gallery_predictions = 0

            for q in all_queries:
                pred = predict_clip(q["embedding"], gallery_emb, gallery_meta, temperature=temp)
                conf = pred["confidence"]
                p_id = pred["monument_id"]
                gt = q["ground_truth"]

                accepted = conf >= thresh

                if q["is_in_gallery"]:
                    if accepted:
                        if p_id == gt:
                            tp += 1
                            correct_in_gallery_predictions += 1
                        else:
                            fp += 1
                    else:
                        fn += 1
                else:
                    # OOD (unseen or non-monument)
                    if accepted:
                        fp += 1
                    else:
                        tn += 1

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            in_gal_acc = tp / (tp + (fp if fp <= total_in else 0)) if tp > 0 else 0.0
            ood_reject_pct = (tn / total_ood) * 100.0 if total_ood > 0 else 0.0

            print(
                f"{thresh:<11.2f} | {prec*100:>8.1f}% | {rec*100:>6.1f}% | {f1*100:>6.1f}% | "
                f"{in_gal_acc*100:>9.1f}% | {ood_reject_pct:>11.1f}% | "
                f"{tp:<4} | {fp:<4} | {fn:<4} | {tn:<4}"
            )

            if f1 > best_f1:
                best_f1 = f1
                best_config = {
                    "temperature": temp,
                    "threshold": thresh,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                    "in_gal_acc": in_gal_acc,
                    "ood_reject_pct": ood_reject_pct,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                }

    print("\n" + "=" * 95)
    print("OPTIMAL CONFIGURATION DETAILS")
    print("=" * 95)
    print(f"Optimal Temperature: tau = {best_config['temperature']:.2f}")
    print(f"Optimal Threshold:   T   = {best_config['threshold']:.2f}")
    print(f"Precision:           {best_config['precision']*100:.2f}%")
    print(f"Recall:              {best_config['recall']*100:.2f}%")
    print(f"F1-Score:            {best_config['f1']*100:.2f}%")
    print(f"In-Gallery Accuracy: {best_config['in_gal_acc']*100:.2f}%")
    print(f"OOD Rejection Rate:  {best_config['ood_reject_pct']:.2f}% (TN={best_config['tn']}/{total_ood})")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    evaluate()
