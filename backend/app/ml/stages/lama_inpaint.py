"""
Native self-contained LaMa Inpainting runner.
Avoids external 'simple-lama-inpainting' package dependency conflicts with modern Pillow versions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
import torch
from PIL import Image
from torch.hub import download_url_to_file, get_dir

LAMA_MODEL_URL = os.environ.get(
    "LAMA_MODEL_URL",
    "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt",
)


def get_image(image: Image.Image | np.ndarray) -> np.ndarray:
    if isinstance(image, Image.Image):
        img = np.array(image)
    elif isinstance(image, np.ndarray):
        img = image.copy()
    else:
        raise ValueError("Input image must be a PIL Image or numpy array!")

    if img.ndim == 3:
        img = np.transpose(img, (2, 0, 1))  # (C, H, W)
    elif img.ndim == 2:
        img = img[np.newaxis, ...]

    return img.astype(np.float32) / 255.0


def ceil_modulo(x: int, mod: int) -> int:
    return x if x % mod == 0 else (x // mod + 1) * mod


def pad_img_to_modulo(img: np.ndarray, mod: int) -> np.ndarray:
    channels, height, width = img.shape
    out_height = ceil_modulo(height, mod)
    out_width = ceil_modulo(width, mod)
    return np.pad(
        img,
        ((0, 0), (0, out_height - height), (0, out_width - width)),
        mode="symmetric",
    )


def prepare_img_and_mask(
    image: Image.Image | np.ndarray,
    mask: Image.Image | np.ndarray,
    device: torch.device,
    pad_out_to_modulo: int = 8,
) -> tuple[torch.Tensor, torch.Tensor]:
    out_image = get_image(image)
    out_mask = get_image(mask)

    if pad_out_to_modulo > 1:
        out_image = pad_img_to_modulo(out_image, pad_out_to_modulo)
        out_mask = pad_img_to_modulo(out_mask, pad_out_to_modulo)

    t_image = torch.from_numpy(out_image).unsqueeze(0).to(device)
    t_mask = torch.from_numpy(out_mask).unsqueeze(0).to(device)
    t_mask = (t_mask > 0).float()

    return t_image, t_mask


def download_lama_model(url: str = LAMA_MODEL_URL) -> str:
    parts = urlparse(url)
    hub_dir = get_dir()
    model_dir = os.path.join(hub_dir, "checkpoints")
    os.makedirs(model_dir, exist_ok=True)
    filename = os.path.basename(parts.path)
    cached_file = os.path.join(model_dir, filename)

    if not os.path.exists(cached_file):
        sys.stderr.write(f'Downloading LaMa model: "{url}" to {cached_file}\n')
        download_url_to_file(url, cached_file, progress=True)

    return cached_file


class SimpleLama:
    """Self-contained TorchScript LaMa inpainting model runner."""

    def __init__(self, device: torch.device | None = None) -> None:
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model_env = os.environ.get("LAMA_MODEL")
        if model_env and os.path.exists(model_env):
            model_path = model_env
        else:
            model_path = download_lama_model(LAMA_MODEL_URL)

        self.device = device
        self.model = torch.jit.load(model_path, map_location=device)
        self.model.eval()
        self.model.to(device)

    def __call__(self, image: Image.Image | np.ndarray, mask: Image.Image | np.ndarray) -> Image.Image:
        orig_w, orig_h = image.size if isinstance(image, Image.Image) else (image.shape[1], image.shape[0])
        t_img, t_mask = prepare_img_and_mask(image, mask, self.device)

        with torch.inference_mode():
            inpainted = self.model(t_img, t_mask)
            res = inpainted[0].permute(1, 2, 0).detach().cpu().numpy()
            res = np.clip(res * 255.0, 0, 255).astype(np.uint8)

        # Crop out any modulo padding
        res = res[:orig_h, :orig_w]
        return Image.fromarray(res)
