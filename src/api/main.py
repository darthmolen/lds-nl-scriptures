"""FastAPI application entry point.

Provides the main FastAPI application factory and app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings
from src.api.routers import cfm, conference, health, scriptures


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Semantic search API for scriptures, Come Follow Me lessons, and General Conference talks.",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(scriptures.router, prefix="/api/v1")
    app.include_router(cfm.router, prefix="/api/v1")
    app.include_router(conference.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint returning API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    return app


# Create the app instance for uvicorn
app = create_app()
