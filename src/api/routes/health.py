"""
Health check endpoints.
"""
from fastapi import APIRouter, status

from src.api.schemas import HealthResponse
from src.config.settings import get_settings
from src.retrieval.qdrant_client import get_qdrant_client

router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint."""
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check endpoint.

    Verifies that all dependencies are available.
    """
    settings = get_settings()

    # Check Qdrant connection
    try:
        client = get_qdrant_client()
        collections = client.get_collections()

        # Verify our collection exists
        collection_exists = any(
            c.name == settings.qdrant_collection_name for c in collections.collections
        )

        if not collection_exists:
            return {
                "status": "not_ready",
                "reason": f"Collection '{settings.qdrant_collection_name}' not found",
            }, status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "ready",
            "checks": {
                "qdrant": "ok",
                "collection": "ok",
            },
        }

    except Exception as e:
        return {
            "status": "not_ready",
            "reason": f"Qdrant connection failed: {str(e)}",
        }, status.HTTP_503_SERVICE_UNAVAILABLE
