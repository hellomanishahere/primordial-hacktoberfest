"""FastAPI Application entrypoint for Primordial Decision Intelligence."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import PrimordialException
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup and shutdown routines."""
    setup_logging()
    logger.info("Starting Primordial Backend v%s in %s environment", settings.VERSION, settings.APP_ENV)
    yield
    logger.info("Shutting down Primordial Backend")


def create_application() -> FastAPI:
    """Factory creating and configuring the FastAPI application instance."""
    app = FastAPI(
        title="Primordial API",
        description="Open Source Decision Intelligence and Knowledge Recovery System",
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS: restrictive origins parsed from environment configuration
    origins = [orig.strip() for orig in settings.CORS_ALLOWED_ORIGINS.split(",") if orig.strip()]
    allow_all = "*" in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not allow_all else ["*"],
        allow_credentials=not allow_all,  # Only allow credentials if origins are explicitly restricted
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    @app.exception_handler(PrimordialException)
    async def primordial_exception_handler(request: Request, exc: PrimordialException) -> JSONResponse:
        logger.warning(
            "PrimordialException on %s %s: [%s] %s",
            request.method,
            request.url.path,
            exc.error_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Invalid request payload or parameters",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning("HTTPException on %s %s: %s - %s", request.method, request.url.path, exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
                "details": {},
            },
        )

    # Mount API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    from app.api.endpoints import radar
    app.include_router(radar.router, prefix="/api/radar", tags=["PR Radar"])

    # Root informational endpoint
    @app.get(
        "/",
        tags=["System"],
        summary="Service Root Info",
        description="Returns basic service metadata and documentation links.",
    )
    async def root_info() -> dict:
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.APP_ENV,
            "docs_url": "/docs",
            "health_check": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()
