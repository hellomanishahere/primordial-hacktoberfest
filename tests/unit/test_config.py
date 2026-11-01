"""Unit tests for centralized configuration."""

from app.core.config import Settings, settings


def test_default_settings():
    """Verify that default settings match documented standards."""
    assert settings.APP_NAME == "Primordial"
    assert settings.APP_ENV in ["development", "test", "production"]
    assert settings.APP_PORT == 8000
    assert settings.APP_HOST == "127.0.0.1"
    assert settings.CORS_ALLOWED_ORIGINS == "http://localhost:5173,http://127.0.0.1:5173"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.VERSION == "0.1.0"
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
    assert settings.AI_MODEL_PRIMARY == "qwen2.5:7b"
    assert settings.AI_TIMEOUT_SECONDS == 90
    assert settings.ENABLE_WAL_MODE is True


def test_custom_settings_override(monkeypatch):
    """Verify that environment variables override settings."""
    monkeypatch.setenv("APP_NAME", "CustomPrimordial")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_MODEL_PRIMARY", "custom-model:latest")

    custom = Settings()
    assert custom.APP_NAME == "CustomPrimordial"
    assert custom.APP_PORT == 9000
    assert custom.APP_ENV == "test"
    assert custom.AI_MODEL_PRIMARY == "custom-model:latest"

