"""
Multi-layer caching for embeddings, tool results, and responses.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.config.settings import get_settings


class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if datetime.now() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        expiry = datetime.now() + timedelta(seconds=self._ttl_seconds)
        self._cache[key] = (value, expiry)

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()

    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)


class EmbeddingCache(SimpleCache):
    """Cache for embeddings."""

    def __init__(self):
        settings = get_settings()
        super().__init__(ttl_seconds=settings.cache_ttl_seconds)

    @staticmethod
    def _hash_text(text: str) -> str:
        """Create hash of text for cache key."""
        return hashlib.sha256(text.encode()).hexdigest()

    def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get cached embedding."""
        key = self._hash_text(text)
        return self.get(key)

    def set_embedding(self, text: str, embedding: list[float]) -> None:
        """Cache embedding."""
        key = self._hash_text(text)
        self.set(key, embedding)


class ToolResultCache(SimpleCache):
    """Cache for tool results."""

    def __init__(self):
        settings = get_settings()
        super().__init__(ttl_seconds=settings.cache_ttl_seconds)


class ResponseCache(SimpleCache):
    """Cache for full responses."""

    def __init__(self):
        # Shorter TTL for responses (1 minute)
        super().__init__(ttl_seconds=60)

    @staticmethod
    def _create_key(message: str, property_id: str, reservation_id: str | None) -> str:
        """Create cache key from request parameters."""
        key_str = f"{message}:{property_id}:{reservation_id or ''}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get_response(
        self, message: str, property_id: str, reservation_id: str | None
    ) -> Optional[dict]:
        """Get cached response."""
        key = self._create_key(message, property_id, reservation_id)
        return self.get(key)

    def set_response(
        self, message: str, property_id: str, reservation_id: str | None, response: dict
    ) -> None:
        """Cache response."""
        key = self._create_key(message, property_id, reservation_id)
        self.set(key, response)


# Global cache instances
embedding_cache = EmbeddingCache()
tool_result_cache = ToolResultCache()
response_cache = ResponseCache()


# Common queries for cache warming
# These cover the most frequent guest inquiries
COMMON_QUERIES = [
    # Check-in/out
    "What time is check-in?",
    "What time is checkout?",
    "What time is check in?",
    "What time is check out?",
    "When is check-in?",
    "When is checkout?",
    "Can I check in early?",
    "Can I check out late?",
    "What is the check-in time?",
    "What is the checkout time?",
    "Early check-in",
    "Late checkout",
    # Parking
    "Is there parking available?",
    "Is there parking?",
    "Do you have parking?",
    "Where can I park?",
    "Is parking free?",
    "How much is parking?",
    # WiFi
    "What is the wifi password?",
    "What's the wifi password?",
    "WiFi password?",
    "How do I connect to wifi?",
    "Is there wifi?",
    "Do you have internet?",
    # Amenities
    "What amenities are available?",
    "What amenities do you have?",
    "Is there a pool?",
    "Is there a gym?",
    "Do you have a fitness center?",
    "Is breakfast included?",
    "Do you serve breakfast?",
    # Room info
    "What type of bed is in the room?",
    "Is there air conditioning?",
    "Is there a kitchen?",
    "Does the room have a balcony?",
    "How many beds?",
    # Policies
    "What is the cancellation policy?",
    "Can I cancel my reservation?",
    "Are pets allowed?",
    "Do you allow pets?",
    "Is smoking allowed?",
    "What are the house rules?",
    # Location
    "What is the address?",
    "Where are you located?",
    "How do I get there?",
    "How far from the airport?",
    "Is there public transport nearby?",
    # Contact
    "How can I contact you?",
    "What is your phone number?",
    "What is your email?",
    # General
    "Hello",
    "Hi",
    "Thank you",
    "Thanks",
]


async def warm_embedding_cache() -> int:
    """
    Pre-generate embeddings for common queries at startup.

    Returns:
        Number of embeddings generated
    """
    from src.retrieval.embeddings import generate_embeddings
    from src.monitoring.logging import get_logger

    logger = get_logger(__name__)

    # Filter out queries that are already cached
    queries_to_warm = [
        q for q in COMMON_QUERIES
        if embedding_cache.get_embedding(q) is None
    ]

    if not queries_to_warm:
        logger.info("Embedding cache already warm, no queries to generate")
        return 0

    logger.info(f"Warming embedding cache with {len(queries_to_warm)} queries...")

    try:
        # Generate embeddings in batch (more efficient)
        embeddings = await generate_embeddings(queries_to_warm)

        # Cache each embedding
        for query, embedding in zip(queries_to_warm, embeddings):
            embedding_cache.set_embedding(query, embedding)

        logger.info(f"Embedding cache warmed successfully with {len(queries_to_warm)} queries")
        return len(queries_to_warm)
    except Exception as e:
        logger.error(f"Failed to warm embedding cache: {e}")
        return 0
