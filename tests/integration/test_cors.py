"""CORS policy checks for the local-first API."""

import pytest


@pytest.mark.asyncio
async def test_allows_configured_local_frontend_origin(async_client):
    response = await async_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.asyncio
async def test_does_not_allow_arbitrary_origins(async_client):
    response = await async_client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
