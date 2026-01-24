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
