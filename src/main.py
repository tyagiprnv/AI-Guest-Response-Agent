"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.api.middleware import setup_middleware
from src.api.routes import health, response
from src.config.settings import get_settings
from src.monitoring.langsmith import setup_langsmith
from src.monitoring.logging import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Guest Response Agent...")
    settings = get_settings()

    # Set up LangSmith tracing
    try:
        setup_langsmith()
        logger.info("LangSmith tracing enabled")
    except Exception as e:
        logger.warning(f"LangSmith setup failed: {e}")

    # Warm embedding cache for common queries
    try:
        from src.data.cache import warm_embedding_cache
        warmed_count = await warm_embedding_cache()
        if warmed_count > 0:
            logger.info(f"Embedding cache warmed with {warmed_count} common queries")
    except Exception as e:
        logger.warning(f"Embedding cache warming failed: {e}")

    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="AI Guest Response Agent",
    description="Production-quality AI agent for generating responses to guest accommodation inquiries",
    version="0.1.0",
    lifespan=lifespan,
)

# Set up middleware
setup_middleware(app)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(response.router, prefix="/api/v1", tags=["Response"])


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to docs."""
    return {
        "message": "AI Guest Response Agent API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
    )
