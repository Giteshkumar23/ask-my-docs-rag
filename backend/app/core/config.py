"""Application configuration via pydantic-settings.

All settings are read from environment variables (or a .env file).
Never hardcode secrets — use environment variables in production.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object.  Loaded once and cached via :func:`get_settings`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Core application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "Ask My Docs"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = Field(..., description="Secret key for signing tokens — required")

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = Field(..., description="PostgreSQL async DSN (asyncpg)")

    # ------------------------------------------------------------------ #
    # Redis / Celery
    # ------------------------------------------------------------------ #
    REDIS_URL: str = "redis://localhost:6379"

    # ------------------------------------------------------------------ #
    # LLM providers
    # ------------------------------------------------------------------ #
    LLM_PROVIDER: str = Field(
        default="openai",
        description="One of: openai | groq | gemini | ollama",
    )
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ------------------------------------------------------------------ #
    # Models
    # ------------------------------------------------------------------ #
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL: str = "gpt-4o-mini"

    # ------------------------------------------------------------------ #
    # File uploads
    # ------------------------------------------------------------------ #
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "uploads"

    # ------------------------------------------------------------------ #
    # Chunking
    # ------------------------------------------------------------------ #
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    BM25_WEIGHT: float = 0.4
    VECTOR_WEIGHT: float = 0.6
    TOP_K_RETRIEVAL: int = 20
    TOP_K_FINAL: int = 5

    # ------------------------------------------------------------------ #
    # API / Security
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # ------------------------------------------------------------------ #
    # Observability
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------ #
    # Computed
    # ------------------------------------------------------------------ #
    @computed_field  # type: ignore[misc]
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:  # noqa: N802
        """Derived from MAX_FILE_SIZE_MB."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @model_validator(mode="after")
    def _validate_llm_provider(self) -> "Settings":
        valid = {"openai", "groq", "gemini", "ollama"}
        if self.LLM_PROVIDER not in valid:
            raise ValueError(
                f"LLM_PROVIDER must be one of {valid}, got '{self.LLM_PROVIDER}'"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached :class:`Settings` singleton."""
    return Settings()  # type: ignore[call-arg]


# Convenience alias used throughout the application
settings: Settings = get_settings()
