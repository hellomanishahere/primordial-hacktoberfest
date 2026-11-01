"""Top-level API router mounting v1 endpoints."""

from fastapi import APIRouter
from app.api.endpoints import decisions, extract, health, overview, radar

api_router = APIRouter()

# Mount health endpoint under /api/v1/health
api_router.include_router(health.router, tags=["Health"])

# Mount pipeline extraction endpoint under /api/v1/extract
api_router.include_router(extract.router, tags=["Extraction"])

# Mount decisions and search under /api/v1/decisions
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])

# Mount overview stats under /api/v1/overview
api_router.include_router(overview.router, tags=["Overview"])

# Mount PR Radar endpoints under /api/v1/radar
api_router.include_router(radar.router, prefix="/radar", tags=["PR Radar"])

