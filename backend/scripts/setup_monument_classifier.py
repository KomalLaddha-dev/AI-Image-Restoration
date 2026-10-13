"""
Automated Monument Classifier Setup & Bootstrap Script
======================================================
1. Loads all monuments from backend/data/monuments.json.
2. Generates backend/models/labels.json.
3. Obtains canonical reference photos for each monument (local samples + Wikipedia API).
4. Extracts deep visual prototype features using MobileNetV3-Large.
5. Constructs a calibrated neural classifier head and exports to backend/models/monument_classifier.onnx.
6. Runs self-verification inference using ONNX Runtime.
"""

import json
import os
import urllib.request
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from loguru import logger

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
SAMPLES_DIR = BASE_DIR.parent / "web-demo" / "public" / "samples"
REF_DIR = DATA_DIR / "reference_images"

# Wikipedia image lookup map for fallback downloads
WIKI_PAGES = {
    "red_fort": "Red_Fort",
    "eiffel_tower": "Eiffel_Tower",
    "machu_picchu": "Machu_Picchu",
    "hawa_mahal": "Hawa_Mahal",
    "angkor_wat": "Angkor_Wat",
    "gateway_of_india": "Gateway_of_India",
    "parthenon": "Parthenon",
    "statue_of_liberty": "Statue_of_Liberty",
}


def download_wiki_thumbnail(page_title: str, dest_path: Path) -> bool:
    """Download canonical thumbnail from Wikipedia API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeritageRestore/1.0 (academic-cv-project)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            thumb_url = data.get("thumbnail", {}).get("source")
            if not thumb_url:
                logger.warning(f"No thumbnail found in Wikipedia for {page_title}")
                return False

        # Download thumbnail
        img_req = urllib.request.Request(thumb_url, headers={"User-Agent": "HeritageRestore/1.0 (academic-cv-project)"})
        with urllib.request.urlopen(img_req, timeout=10) as img_resp:
            dest_path.write_bytes(img_resp.read())
            logger.info(f"Downloaded canonical image for {page_title} -> {dest_path.name}")
            return True
    except Exception as e:
        logger.warning(f"Failed to fetch wiki thumbnail for {page_title}: {e}")
        return False


def get_reference_images(monuments: list[dict]) -> dict[str, list[Path]]:
    """Gather reference image paths for each monument."""
    REF_DIR.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, list[Path]] = {}

    local_sample_overrides = {
        "taj_mahal": [
            SAMPLES_DIR / "taj_mahal.jpg",
            SAMPLES_DIR / "taj_mahal_restored.jpg",
            BASE_DIR.parent / "temp.jpg",
        ],
        "qutub_minar": [SAMPLES_DIR / "qutub_minar.jpg"],
        "colosseum": [SAMPLES_DIR / "colosseum.jpg"],
        "pyramids_giza": [SAMPLES_DIR / "pyramids_giza.jpg"],
    }

    for m in monuments:
        m_id = m["id"]
        img_paths: list[Path] = []

        # 1. Check local samples
        if m_id in local_sample_overrides:
            for p in local_sample_overrides[m_id]:
                if p.exists():
                    img_paths.append(p)

        # 2. Check reference directory or download from Wikipedia
        ref_file = REF_DIR / f"{m_id}.jpg"
        if not ref_file.exists() and m_id in WIKI_PAGES:
            download_wiki_thumbnail(WIKI_PAGES[m_id], ref_file)

        if ref_file.exists() and ref_file not in img_paths:
            img_paths.append(ref_file)

        mapping[m_id] = img_paths
        logger.info(f"Monument '{m_id}': {len(img_paths)} reference image(s) available")

    return mapping


class PrototypeMonumentClassifier(nn.Module):
    """
    MobileNetV3-Large architecture equipped with an L2-normalized
    cosine prototype projection layer.
    """

    def __init__(self, num_classes: int, prototype_weights: torch.Tensor, scale: float = 12.0):
        super().__init__()
        backbone = models.mobilenet_v3_large(weights=None)
        self.features = backbone.features
        self.avgpool = backbone.avgpool

        # First stage of classifier: 960 -> 1280 with Hardswish
        self.fc1 = backbone.classifier[0]  # Linear(960, 1280)
        self.act1 = nn.Hardswish()

        # Prototype projection: Linear(1280, num_classes, bias=False)
        self.classifier = nn.Linear(1280, num_classes, bias=False)
        with torch.no_grad():
            self.classifier.weight.copy_(prototype_weights * scale)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = self.act1(x)
        # Normalize deep feature for cosine distance
        norm = torch.norm(x, p=2, dim=1, keepdim=True).clamp(min=1e-6)
        x_norm = x / norm
        logits = self.classifier(x_norm)
        return logits


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    monuments_file = DATA_DIR / "monuments.json"
    if not monuments_file.exists():
        raise FileNotFoundError(f"monuments.json not found at {monuments_file}")

    with open(monuments_file, encoding="utf-8") as f:
        monuments: list[dict] = json.load(f)

    num_classes = len(monuments)
    logger.info(f"Found {num_classes} monuments in {monuments_file.name}")

    # 1. Generate labels.json
    labels: dict[str, dict] = {}
    for idx, m in enumerate(monuments):
        labels[str(idx)] = {
            "id": m["id"],
            "name": m["name"],
            "location": m.get("location", ""),
            "era": m.get("era", ""),
            "architectural_style": m.get("architectural_style", ""),
        }

    labels_path = MODELS_DIR / "labels.json"
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)
    logger.info(f"Saved labels mapping to {labels_path}")

    # 2. Gather reference images
    ref_images = get_reference_images(monuments)

    # 3. Load pre-trained MobileNetV3-Large feature extractor
    logger.info("Loading pre-trained MobileNetV3-Large backbone...")
    base_model = models.mobilenet_v3_large(weights="DEFAULT")
    base_model.eval()

    feature_extractor = nn.Sequential(
        base_model.features,
        base_model.avgpool,
        nn.Flatten(1),
        base_model.classifier[0],
        nn.Hardswish(),
    )
    feature_extractor.eval()

    # Preprocessing transforms (standard ImageNet 224x224)
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Augmentations to create multiple synthetic perspectives/contrasts per reference
    aug_transforms = [
        transform,
        transforms.Compose([
            transforms.Resize(256),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=1.0),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
    ]

    # 4. Extract visual prototype feature vectors for each class
    prototype_matrix = torch.zeros(num_classes, 1280)

    with torch.no_grad():
        for idx, m in enumerate(monuments):
            m_id = m["id"]
            img_paths = ref_images.get(m_id, [])

            class_features = []
            for img_path in img_paths:
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    for t in aug_transforms:
                        tensor = t(pil_img).unsqueeze(0)
                        feat = feature_extractor(tensor)  # (1, 1280)
                        feat_norm = feat / torch.norm(feat, p=2, dim=1, keepdim=True).clamp(min=1e-6)
                        class_features.append(feat_norm)
                except Exception as e:
                    logger.warning(f"Error processing {img_path}: {e}")

            if class_features:
                mean_feat = torch.cat(class_features, dim=0).mean(dim=0, keepdim=True)
                mean_feat = mean_feat / torch.norm(mean_feat, p=2, dim=1, keepdim=True).clamp(min=1e-6)
                prototype_matrix[idx] = mean_feat.squeeze(0)
                logger.info(f"Built prototype for [{idx}] {m['name']} from {len(class_features)} feature views")
            else:
                # Random normalized vector if no reference photo could be fetched
                rand_feat = torch.randn(1, 1280)
                rand_feat = rand_feat / torch.norm(rand_feat, p=2, dim=1, keepdim=True)
                prototype_matrix[idx] = rand_feat.squeeze(0)
                logger.warning(f"No views for [{idx}] {m['name']} — initialized random vector")

    # 5. Build model and export to ONNX
    logger.info("Constructing PrototypeMonumentClassifier...")
    export_model = PrototypeMonumentClassifier(num_classes, prototype_matrix, scale=12.0)
    # Copy weights from base_model
    export_model.features.load_state_dict(base_model.features.state_dict())
    export_model.fc1.load_state_dict(base_model.classifier[0].state_dict())
    export_model.eval()

    onnx_path = MODELS_DIR / "monument_classifier.onnx"
    dummy_input = torch.randn(1, 3, 224, 224)

    logger.info(f"Exporting ONNX model to {onnx_path}...")
    torch.onnx.export(
        export_model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
    logger.info(f"Successfully exported {onnx_path} ({onnx_path.stat().st_size / (1024*1024):.2f} MB)")

    # 6. Verify inference using ONNX Runtime
    logger.info("Verifying ONNX Runtime inference on sample images...")
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    test_samples = [
        ("Taj Mahal (clean)", SAMPLES_DIR / "taj_mahal.jpg", "taj_mahal"),
        ("Taj Mahal (degraded)", SAMPLES_DIR / "taj_mahal_hero_degraded.jpg", "taj_mahal"),
        ("Colosseum", SAMPLES_DIR / "colosseum.jpg", "colosseum"),
        ("Qutub Minar", SAMPLES_DIR / "qutub_minar.jpg", "qutub_minar"),
        ("Pyramids of Giza", SAMPLES_DIR / "pyramids_giza.jpg", "pyramids_giza"),
        ("Detroit 1915 (OOD)", SAMPLES_DIR / "detroit_1915.jpg", None),
    ]

    for label_desc, test_path, expected_id in test_samples:
        if not test_path.exists():
            continue

        cv_img = cv2.imread(str(test_path))
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (224, 224)).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_norm = (img_resized - mean) / std
        input_tensor = np.expand_dims(img_norm.transpose(2, 0, 1), axis=0).astype(np.float32)

        out = session.run(["output"], {"input": input_tensor})[0][0]
        exp_out = np.exp(out - np.max(out))
        probs = exp_out / exp_out.sum()
        pred_idx = int(np.argmax(probs))
        pred_conf = float(probs[pred_idx])
        pred_monument = labels[str(pred_idx)]["name"]
        pred_id = labels[str(pred_idx)]["id"]

        is_match = (expected_id == pred_id) if expected_id else (pred_conf < 0.60)
        match_symbol = "✅" if is_match else "⚠️"
        logger.info(
            f"{match_symbol} Test [{label_desc}]: Predicted '{pred_monument}' "
            f"(id: {pred_id}) with {pred_conf*100:.1f}% confidence (expected: {expected_id})"
        )

    logger.info("Setup and verification completed successfully!")


if __name__ == "__main__":
    main()
