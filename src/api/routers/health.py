"""Health check router.

Provides endpoints for basic health checks and readiness probes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.config import get_settings
from src.api.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint.

    Returns a simple status indicating the API is running.
    This endpoint does not check external dependencies.

    Returns:
        dict: Status and version information.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity.

    Verifies that the database is accessible and responding.
    Use this endpoint for Kubernetes readiness probes.

    Args:
        db: Database session dependency.

    Returns:
        dict: Status and details about database connectivity.

    Raises:
        HTTPException: 503 if database is not reachable.
    """
    try:
        # Execute a simple query to verify database connectivity
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not ready",
                "database": "disconnected",
                "error": str(e),
            },
        )
