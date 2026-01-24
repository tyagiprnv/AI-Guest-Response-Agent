"""
Unit tests for caching.
"""
import pytest
import asyncio

from src.data.cache import SimpleCache, EmbeddingCache, ResponseCache


def test_simple_cache():
    """Test SimpleCache basic functionality."""
    cache = SimpleCache(ttl_seconds=60)

    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test non-existent key
    assert cache.get("key2") is None

    # Test size
    assert cache.size() == 1

    # Test clear
    cache.clear()
    assert cache.size() == 0


def test_embedding_cache():
    """Test EmbeddingCache."""
    cache = EmbeddingCache()

    text = "What time is check-in?"
    embedding = [0.1, 0.2, 0.3]

    # Set and get embedding
    cache.set_embedding(text, embedding)
    retrieved = cache.get_embedding(text)

    assert retrieved == embedding

    # Different text should not match
    assert cache.get_embedding("Different text") is None


def test_response_cache():
    """Test ResponseCache."""
    cache = ResponseCache()

    message = "What time is check-in?"
    property_id = "prop_001"
    reservation_id = "res_001"

    response = {
        "response_text": "Check-in is at 3:00 PM",
        "response_type": "template",
        "confidence_score": 0.9,
    }

    # Set and get response
    cache.set_response(message, property_id, reservation_id, response)
    retrieved = cache.get_response(message, property_id, reservation_id)

    assert retrieved == response

    # Different parameters should not match
    assert cache.get_response(message, "prop_002", reservation_id) is None
