"""FastAPI application for Azure Cloud Booking Service."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from prometheus_client import make_asgi_app

from app.api.v1 import router as api_v1_router
from app.config import settings
from app.database import db
from app.unified_log_queue import log_sender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logs (only show warnings and errors)
logging.getLogger("azure").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Debug mode: %s", settings.debug)

    # Initialize database tables
    try:
        logger.info("Initializing database tables...")
        db.create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.exception("Failed to initialize database tables: %s", str(e))
        # Don't raise - allow app to start even if tables already exist
        # SQLAlchemy's create_all() is idempotent, but log any unexpected errors
        if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
            logger.warning("Database table creation encountered an error, but continuing startup")

    if log_sender:
        logger.info("Sending grooming service startup log event...")
        await log_sender.send(
            level="info",
            event="grooming-service.startup",
            message="Grooming service startup complete",
            context={
                "database_url": settings.db_connection_string,
            },
        )

    yield  # Application runs here

    # Shutdown
    logger.info("Application shutdown complete")
    if log_sender:
        logger.info("Sending grooming service shutdown log event...")
        await log_sender.send(
            level="info",
            event="grooming-service.shutdown",
            message="Grooming service shutdown complete",
        )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pet grooming service with Azure SQL integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Include API v1 router
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

app.mount("/metrics", make_asgi_app())


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
