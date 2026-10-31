"""Top-level API router mounting v1 endpoints."""

from fastapi import APIRouter
from app.api.endpoints import health

api_router = APIRouter()

# Mount health endpoint under /api/v1/health
api_router.include_router(health.router, tags=["Health"])

