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


def is_grayscale_or_sepia(img: np.ndarray, std_threshold: float = 5.0) -> tuple[bool, float]:
    """
    Check if an image is grayscale or sepia based on chrominance variance.
    Returns (is_needs_colorization, chroma_std).
    Historical sepia photos and faded black-and-white photos have low chrominance variance.
    """
    if len(img.shape) == 2 or img.shape[2] == 1:
        return True, 0.0
    
    # Convert to LAB to measure chrominance variance
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    # Calculate standard deviation of A and B channels
    std_a = np.std(lab[:, :, 1])
    std_b = np.std(lab[:, :, 2])
    
    chroma_std = float((std_a + std_b) / 2.0)
    
    return chroma_std < std_threshold, chroma_std


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
