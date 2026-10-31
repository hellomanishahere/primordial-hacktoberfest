"""Centralized application configuration loaded from environment variables."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    # Application Configuration
    APP_NAME: str = "Primordial"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # GitHub API Configuration (Read-only token; increases limit to 5,000 req/hr)
    GITHUB_TOKEN: Optional[str] = None

    # AI Model Configuration (Local Ollama daemon)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    AI_MODEL_PRIMARY: str = "qwen2.5:7b"
    AI_MODEL_FALLBACK: str = "llama3.1:8b"
    AI_TIMEOUT_SECONDS: int = 90

    # Database Configuration (Phase 2 SQLite WAL mode)
    DATABASE_URL: str = "sqlite:///./primordial.db"
    ENABLE_WAL_MODE: bool = True

    # Demonstration Fallback (Offline fixtures for judging resilience)
    ENABLE_OFFLINE_DEMO_FIXTURES: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

