"""
Cache factory to create cache instances based on configuration.
"""
from functools import lru_cache

from src.config.settings import get_settings


@lru_cache(maxsize=1)
def create_embedding_cache():
    """Create embedding cache based on configuration."""
    settings = get_settings()
    if settings.cache_backend == "redis":
        from src.data.cache_redis import RedisEmbeddingCache

        return RedisEmbeddingCache()
    else:
        from src.data.cache import EmbeddingCache

        return EmbeddingCache()


@lru_cache(maxsize=1)
def create_tool_result_cache():
    """Create tool result cache based on configuration."""
    settings = get_settings()
    if settings.cache_backend == "redis":
        from src.data.cache_redis import RedisToolResultCache

        return RedisToolResultCache()
    else:
        from src.data.cache import ToolResultCache

        return ToolResultCache()


@lru_cache(maxsize=1)
def create_response_cache():
    """Create response cache based on configuration."""
    settings = get_settings()
    if settings.cache_backend == "redis":
        from src.data.cache_redis import RedisResponseCache

        return RedisResponseCache()
    else:
        from src.data.cache import ResponseCache

        return ResponseCache()


# Global cache instances (lazy loaded based on config)
def get_embedding_cache():
    """Get embedding cache instance."""
    return create_embedding_cache()


def get_tool_result_cache():
    """Get tool result cache instance."""
    return create_tool_result_cache()


def get_response_cache():
    """Get response cache instance."""
    return create_response_cache()
