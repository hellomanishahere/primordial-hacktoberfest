"""Integration tests for FastAPI application and health endpoint."""

import pytest
import httpx
from fastapi import FastAPI
from app.core.exceptions import InvalidGitHubURLException


@pytest.mark.asyncio
async def test_app_starts(app: FastAPI):
    """Verify that the FastAPI application initializes correctly with expected attributes."""
    assert app.title == "Primordial API"
    assert app.version == "0.1.0"
    # Verify that routes are registered in OpenAPI specification
    openapi_paths = app.openapi()["paths"]
    assert "/api/v1/health" in openapi_paths
    assert "/" in openapi_paths


@pytest.mark.asyncio
async def test_root_endpoint(async_client: httpx.AsyncClient):
    """Verify that root endpoint GET / returns HTTP 200 and expected metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Primordial"
    assert data["version"] == "0.1.0"
    assert data["health_check"] == "/api/v1/health"


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_and_documented_structure(async_client: httpx.AsyncClient):
    """
    Verify that GET /api/v1/health returns HTTP 200 and matches the documented structure:
    - Overall status
    - App name and version
    - Environment
    - Database component health (SQLite connection check)
    - Ollama component health
    """
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Documented top-level fields
    assert "status" in data
    assert data["status"] == "ok"
    assert data["app"] == "Primordial"
    assert data["version"] == "0.1.0"
    assert data["environment"] in ["development", "test", "production"]

    # Database component verification
    assert "database" in data
    assert "status" in data["database"]
    assert data["database"]["status"] in ["ok", "degraded"]
    assert "details" in data["database"]

    # Ollama component verification
    assert "ollama" in data
    assert "status" in data["ollama"]
    assert data["ollama"]["status"] in ["available", "unreachable", "degraded"]
    assert "details" in data["ollama"]
    assert "url" in data["ollama"]


@pytest.mark.asyncio
async def test_invalid_request_method_handled(async_client: httpx.AsyncClient):
    """Verify that calling POST on GET-only /api/v1/health returns HTTP 405 Method Not Allowed."""
    response = await async_client.post("/api/v1/health", json={"test": "data"})
    assert response.status_code == 405
    data = response.json()
    assert data["error"] == "HTTP_405"
    assert "Method Not Allowed" in data["message"]


@pytest.mark.asyncio
async def test_nonexistent_endpoint_handled(async_client: httpx.AsyncClient):
    """Verify that requests to nonexistent endpoints return HTTP 404 Not Found."""
    response = await async_client.get("/api/v1/nonexistent-endpoint-404")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "HTTP_404"
    assert "Not Found" in data["message"]


@pytest.mark.asyncio
async def test_custom_exception_handling(app: FastAPI, async_client: httpx.AsyncClient):
    """Verify that domain exceptions are caught and formatted into structured JSON envelopes."""
    # Temporarily register a test route that triggers a domain exception
    @app.get("/api/v1/test-error")
    async def trigger_test_error():
        raise InvalidGitHubURLException(
            message="Test malformed URL failure",
            details={"input": "ftp://invalid-url"},
        )

    response = await async_client.get("/api/v1/test-error")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "INVALID_GITHUB_URL"
    assert data["message"] == "Test malformed URL failure"
    assert data["details"] == {"input": "ftp://invalid-url"}
