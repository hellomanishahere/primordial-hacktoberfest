"""Top-level API router mounting v1 endpoints."""

from fastapi import APIRouter
from app.api.endpoints import health, radar

api_router = APIRouter()

# Mount health endpoint under /api/v1/health
api_router.include_router(health.router, tags=["Health"])

# Mount PR Radar endpoints under /api/v1/radar
api_router.include_router(radar.router, prefix="/radar", tags=["PR Radar"])

