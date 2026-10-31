"""Health check endpoint verifying backend, database, and Ollama connectivity."""

import os
import sqlite3
import httpx
from fastapi import APIRouter, status
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.schemas import ComponentHealth, HealthResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Backend Health Check",
    description="Verifies backend status, SQLite database connection, and Ollama service availability.",
)
async def check_health() -> HealthResponse:
    """Verifies backend status, SQLite database connection, and Ollama service availability."""

    # 1. Verify SQLite database connection
    db_status = "ok"
    db_details = f"WAL mode: {settings.ENABLE_WAL_MODE}"
    try:
        raw_db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        # Resolve relative db path if needed
        db_path = os.path.abspath(raw_db_path) if raw_db_path.startswith(".") else raw_db_path
        # Create directory if necessary
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=1.0)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        conn.close()
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        db_status = "degraded"
        db_details = f"Connection error: {str(exc)}"

    # 2. Verify Ollama AI service availability
    ollama_status = "unreachable"
    ollama_details = f"Ollama daemon not reachable at {settings.OLLAMA_BASE_URL}"
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_status = "available"
                ollama_details = f"Connected to {settings.OLLAMA_BASE_URL}"
            else:
                ollama_status = "degraded"
                ollama_details = f"Ollama returned HTTP status {resp.status_code}"
    except Exception as exc:
        logger.debug("Ollama availability check error (expected if daemon not running): %s", exc)
        ollama_status = "unreachable"
        ollama_details = f"Ollama offline at {settings.OLLAMA_BASE_URL}"

    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        database=ComponentHealth(
            status=db_status,
            details=db_details,
        ),
        ollama=ComponentHealth(
            status=ollama_status,
            details=ollama_details,
            url=settings.OLLAMA_BASE_URL,
        ),
    )

