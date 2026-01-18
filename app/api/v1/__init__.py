"""API v1 package."""

from fastapi import APIRouter

from . import health
from .groomers import router as groomers_router
from .reviews import router as reviews_router

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(groomers_router, tags=["groomers"])
router.include_router(reviews_router, tags=["reviews"])


__all__ = ["router"]
