"""
Image utility functions — loading, saving, format conversion between
PIL, NumPy, and OpenCV representations.
"""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from loguru import logger


def load_image_from_bytes(data: bytes) -> np.ndarray:
    """
    Load an image from raw bytes into a BGR NumPy array (OpenCV format).
    Handles JPEG, PNG, WebP, BMP, TIFF.
    """
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image from provided bytes.")
    logger.debug(f"Loaded image: {img.shape[1]}x{img.shape[0]}, dtype={img.dtype}")
    return img


def save_image_to_bytes(img: np.ndarray, fmt: str = ".png") -> bytes:
    """Encode a BGR NumPy array to bytes in the specified format."""
    success, buffer = cv2.imencode(fmt, img)
    if not success:
        raise ValueError(f"Failed to encode image to {fmt}")
    return buffer.tobytes()


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Convert BGR (OpenCV) to RGB."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(img: np.ndarray) -> np.ndarray:
    """Convert RGB to BGR (OpenCV)."""
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


def numpy_to_pil(img: np.ndarray) -> Image.Image:
    """Convert a BGR NumPy array to a PIL Image (RGB)."""
    return Image.fromarray(bgr_to_rgb(img))


def pil_to_numpy(img: Image.Image) -> np.ndarray:
    """Convert a PIL Image (RGB) to a BGR NumPy array."""
    return rgb_to_bgr(np.array(img))


def resize_if_needed(
    img: np.ndarray,
    max_side: int = 2048,
) -> tuple[np.ndarray, float]:
    """
    Downscale an image if its largest side exceeds `max_side`.
    Returns (resized_image, scale_factor).
    Useful for capping input size before heavy ML inference.
    """
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim <= max_side:
        return img, 1.0
    scale = max_side / max_dim
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    logger.debug(f"Resized image from {w}x{h} to {new_w}x{new_h} (scale={scale:.3f})")
    return resized, scale


def is_grayscale_or_sepia(
    img: np.ndarray,
    corr_threshold: float = 0.92,
    sample_pixels: int = 50000,
) -> tuple[bool, float]:
    """
    Check if an image is grayscale or sepia/duotone using inter-channel
    correlation.

    In a grayscale or sepia image every pixel's R, G, B values move
    together — the pixel cloud in RGB space collapses to a line (gray
    axis or a tinted line for sepia).  The mean pairwise Pearson
    correlation among channels is therefore very close to 1.0.

    In a genuinely colorful image, different hues cause the channels to
    diverge across pixels, lowering the correlation.

    This metric is robust to noise level: film grain/staining adds
    per-pixel variance but does NOT decorrelate the channels, so the
    same image measured before and after denoising gives essentially
    the same classification.

    Returns (needs_colorization: bool, mean_channel_corr: float).
    """
    if len(img.shape) == 2 or img.shape[2] == 1:
        return True, 1.0

    # Work in RGB (OpenCV loads BGR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Flatten to (N, 3) and optionally subsample for speed
    pixels = rgb.reshape(-1, 3).astype(np.float64)
    if len(pixels) > sample_pixels:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(pixels), sample_pixels, replace=False)
        pixels = pixels[idx]

    r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]

    def _pearson(x: np.ndarray, y: np.ndarray) -> float:
        """Pearson r, guarded against constant channels."""
        sx, sy = np.std(x), np.std(y)
        if sx < 1e-6 or sy < 1e-6:
            # Both channels are nearly constant — treat as perfectly
            # correlated (uniform-color image → needs colorization).
            return 1.0
        return float(np.corrcoef(x, y)[0, 1])

    corr_rg = _pearson(r, g)
    corr_gb = _pearson(g, b)
    corr_rb = _pearson(r, b)

    mean_corr = (corr_rg + corr_gb + corr_rb) / 3.0

    return mean_corr >= corr_threshold, round(mean_corr, 4)


def detect_faces(img: np.ndarray) -> list[tuple[int, int, int, int]]:
    """
    Simple face detection using OpenCV's Haar cascade.
    Returns list of (x, y, w, h) bounding boxes.
    Used to decide whether to run the face restoration stage.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if isinstance(faces, tuple):
        return []
    return [tuple(f) for f in faces.tolist()]


def save_image_to_file(img: np.ndarray, path: str | Path) -> Path:
    """Save a BGR NumPy array to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)
    logger.debug(f"Saved image to {path}")
    return path

def auto_crop_border(img: np.ndarray) -> np.ndarray:
    """
    Detects and crops out the physical torn-photo print border.
    Uses Canny edge detection and contour finding to locate the main photo content.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    # Dilate edges to connect them
    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img
        
    # Get the bounding box of the largest contour by area
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    
    img_h, img_w = img.shape[:2]
    # Check if the bounding box represents a reasonable crop (at least 60% of image)
    if (w > img_w * 0.6) and (h > img_h * 0.6):
        # Add a tiny margin to avoid keeping the exact edge line
        mx = int(w * 0.015)
        my = int(h * 0.015)
        
        y1 = min(y + my, img_h - 1)
        y2 = max(y + h - my, y1 + 1)
        x1 = min(x + mx, img_w - 1)
        x2 = max(x + w - mx, x1 + 1)
        
        cropped = img[y1:y2, x1:x2]
        logger.info(f"Auto-cropped border: {img_w}x{img_h} -> {x2-x1}x{y2-y1}")
        return cropped
        
    return img
