"""
Redis-backed cache implementations.
"""
import hashlib
import pickle
from typing import Any, Optional

from redis.asyncio import Redis

from src.config.settings import get_settings
from src.data.cache import BaseCache


class RedisCache(BaseCache):
    """Redis-backed cache with TTL."""

    def __init__(self, ttl_seconds: int, prefix: str):
        self._ttl_seconds = ttl_seconds
        self._prefix = prefix
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            settings = get_settings()
            self._redis = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We're using pickle, so we need bytes
            )
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            redis = await self._get_redis()
            value = await redis.get(f"{self._prefix}:{key}")
            if value is None:
                return None
            return pickle.loads(value)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        try:
            redis = await self._get_redis()
            await redis.setex(
                f"{self._prefix}:{key}",
                ttl or self._ttl_seconds,
                pickle.dumps(value),
            )
        except Exception:
            pass

    async def clear(self) -> None:
        """Clear all cache with this prefix."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self._prefix}:*")
            if keys:
                await redis.delete(*keys)
        except Exception:
            pass

    async def size(self) -> int:
        """Get cache size."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self._prefix}:*")
            return len(keys)
        except Exception:
            return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()


class RedisEmbeddingCache(RedisCache):
    """Redis-backed embedding cache."""

    def __init__(self):
        settings = get_settings()
        super().__init__(ttl_seconds=settings.cache_ttl_seconds, prefix="embedding")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for cache key matching."""
        import re

        normalized = text.lower().strip()
        normalized = normalized.replace("-", " ")
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def _hash_text(text: str) -> str:
        """Create hash of normalized text for cache key."""
        normalized = RedisEmbeddingCache._normalize_text(text)
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get cached embedding."""
        key = self._hash_text(text)
        return await self.get(key)

    async def set_embedding(self, text: str, embedding: list[float]) -> None:
        """Cache embedding."""
        key = self._hash_text(text)
        await self.set(key, embedding)


class RedisToolResultCache(RedisCache):
    """Redis-backed tool result cache."""

    def __init__(self):
        settings = get_settings()
        super().__init__(ttl_seconds=settings.cache_ttl_seconds, prefix="tool")


class RedisResponseCache(RedisCache):
    """Redis-backed response cache."""

    def __init__(self):
        super().__init__(ttl_seconds=300, prefix="response")  # Increased from 60s to 5 minutes

    @staticmethod
    def _create_key(message: str, property_id: str, reservation_id: str | None) -> str:
        """Create cache key from request parameters."""
        key_str = f"{message}:{property_id}:{reservation_id or ''}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def get_response(
        self, message: str, property_id: str, reservation_id: str | None
    ) -> Optional[dict]:
        """Get cached response."""
        key = self._create_key(message, property_id, reservation_id)
        return await self.get(key)

    async def set_response(
        self, message: str, property_id: str, reservation_id: str | None, response: dict
    ) -> None:
        """Cache response."""
        key = self._create_key(message, property_id, reservation_id)
        await self.set(key, response)
