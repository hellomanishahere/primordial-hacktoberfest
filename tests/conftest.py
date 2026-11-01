"""Pytest fixtures and configuration."""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI
from app.main import create_application


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Fixture providing the FastAPI application instance."""
    return create_application()


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture providing an async test HTTP client connected to the FastAPI app."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

