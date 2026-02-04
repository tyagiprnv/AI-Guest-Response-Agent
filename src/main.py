"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
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

# Mount data directory for serving JSON files (test_cases.json)
data_dir = Path(__file__).parent.parent / "data"
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")


def custom_openapi():
    """
    Customize OpenAPI schema to include API key authentication.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Define API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": (
                "API key for authentication. "
                "Get your key from the .env file (API_KEYS) or generate one using: "
                "`python scripts/generate_api_key.py`"
            ),
        }
    }

    # Apply security to specific endpoints that use it
    # The /generate-response endpoint already has dependencies=[Depends(get_api_key)]
    # so we just need to mark it in the OpenAPI schema
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            # Check if endpoint uses authentication (has the dependency)
            if path == "/api/v1/generate-response" and method == "post":
                openapi_schema["paths"][path][method]["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set custom OpenAPI schema
app.openapi = custom_openapi


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint serves the frontend demo."""
    from fastapi.responses import FileResponse
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
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
