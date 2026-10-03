"""
Application configuration using Pydantic Settings.
Loads from .env file with sensible defaults for development.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — all values overridable via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Model paths ---
    model_dir: str = "./models"
    device: str = "cpu"  # "cpu" or "cuda"

    # --- Groq API ---
    groq_api_key: str = ""

    # --- Cloudinary ---
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./heritage.db"

    # --- Stretch ---
    replicate_api_token: str = ""
    google_vision_api_key: str = ""

    # --- Generative Enhancement (Colab HYPIR) ---
    colab_hypir_url: str = ""
    colab_hypir_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def model_path(self) -> Path:
        return Path(self.model_dir)

    @property
    def is_gpu_available(self) -> bool:
        return self.device == "cuda"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
