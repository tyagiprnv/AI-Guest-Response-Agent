"""
Qdrant vector database client.
"""
from functools import lru_cache

from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config.settings import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Get cached Qdrant client (sync)."""
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


@lru_cache(maxsize=1)
def get_async_qdrant_client() -> AsyncQdrantClient:
    """Get cached async Qdrant client."""
    settings = get_settings()
    return AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


def create_collection(collection_name: str, vector_size: int) -> None:
    """Create a Qdrant collection."""
    client = get_qdrant_client()

    # Check if collection exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        print(f"Collection '{collection_name}' already exists")
        return

    # Create collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )
    print(f"Created collection '{collection_name}'")


async def upsert_points(
    collection_name: str,
    points: list[PointStruct],
) -> None:
    """Upsert points to collection."""
    client = get_async_qdrant_client()
    await client.upsert(
        collection_name=collection_name,
        points=points,
    )


async def search_similar(
    collection_name: str,
    query_vector: list[float],
    limit: int = 3,
    score_threshold: float | None = None,
) -> list[dict]:
    """Search for similar vectors."""
    client = get_async_qdrant_client()

    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
    )

    return [
        {
            "id": str(result.id),
            "score": result.score,
            "payload": result.payload,
        }
        for result in results
    ]
