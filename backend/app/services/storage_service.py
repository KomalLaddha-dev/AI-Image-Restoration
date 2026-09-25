"""
Image storage service — handles upload to Cloudinary (or local file system as fallback).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from loguru import logger

from app.config import get_settings


class StorageService:
    """Manages image upload and URL generation."""

    def __init__(self):
        self._cloudinary_configured = False
        self._setup_cloudinary()

    def _setup_cloudinary(self) -> None:
        """Configure Cloudinary if credentials are available."""
        settings = get_settings()
        if settings.cloudinary_cloud_name and settings.cloudinary_api_key:
            try:
                import cloudinary
                cloudinary.config(
                    cloud_name=settings.cloudinary_cloud_name,
                    api_key=settings.cloudinary_api_key,
                    api_secret=settings.cloudinary_api_secret,
                    secure=True,
                )
                self._cloudinary_configured = True
                logger.info("Cloudinary configured successfully")
            except ImportError:
                logger.warning("cloudinary package not installed, using local storage")
        else:
            logger.info("Cloudinary not configured — using local file storage")

    async def upload_image(
        self,
        image_bytes: bytes,
        filename: str,
        folder: str = "heritage",
    ) -> str:
        """
        Upload an image and return its public URL.
        Uses Cloudinary if configured, otherwise saves locally.
        """
        if self._cloudinary_configured:
            return await self._upload_to_cloudinary(image_bytes, filename, folder)
        return self._save_locally(image_bytes, filename)

    async def _upload_to_cloudinary(
        self, image_bytes: bytes, filename: str, folder: str
    ) -> str:
        """Upload to Cloudinary and return the secure URL."""
        import cloudinary.uploader

        # Write to temp file (Cloudinary SDK needs a file path)
        tmp = Path(tempfile.gettempdir()) / filename
        tmp.write_bytes(image_bytes)

        try:
            result = cloudinary.uploader.upload(
                str(tmp),
                folder=folder,
                public_id=Path(filename).stem,
                overwrite=True,
                resource_type="image",
            )
            url = result.get("secure_url", result.get("url", ""))
            logger.info(f"Uploaded to Cloudinary: {url}")
            return url
        finally:
            tmp.unlink(missing_ok=True)

    def _save_locally(self, image_bytes: bytes, filename: str) -> str:
        """Save to local static directory and return a relative URL."""
        static_dir = Path("static") / "uploads"
        static_dir.mkdir(parents=True, exist_ok=True)
        filepath = static_dir / filename
        filepath.write_bytes(image_bytes)
        logger.info(f"Saved locally: {filepath}")
        return f"/static/uploads/{filename}"
