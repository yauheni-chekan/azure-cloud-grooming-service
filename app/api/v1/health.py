"""Health check endpoint."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}
