"""
Unit tests for caching.
"""
import pytest
import time

from src.data.cache import SimpleCache, EmbeddingCache, ResponseCache, ToolResultCache


class TestSimpleCache:
    """Test SimpleCache basic functionality."""

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = SimpleCache(ttl_seconds=60)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = SimpleCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_size(self):
        """Test cache size tracking."""
        cache = SimpleCache(ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_clear(self):
        """Test cache clearing."""
        cache = SimpleCache(ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = SimpleCache(ttl_seconds=1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for TTL to expire
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_overwrite_existing_key(self):
        """Test overwriting an existing key."""
        cache = SimpleCache(ttl_seconds=60)

        cache.set("key1", "value1")
        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"


class TestEmbeddingCache:
    """Test EmbeddingCache."""

    def test_set_and_get_embedding(self):
        """Test setting and getting embeddings."""
        cache = EmbeddingCache()
        cache.clear()  # Clear before test

        text = "What time is check-in?"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        cache.set_embedding(text, embedding)
        retrieved = cache.get_embedding(text)

        assert retrieved == embedding

    def test_different_text_no_match(self):
        """Test that different text doesn't match."""
        cache = EmbeddingCache()
        cache.clear()  # Clear before test

        cache.set_embedding("What time is check-in?", [0.1, 0.2, 0.3])
        retrieved = cache.get_embedding("What time is check-out?")

        assert retrieved is None

    def test_same_text_same_hash(self):
        """Test that identical text produces same cache key."""
        cache = EmbeddingCache()
        cache.clear()  # Clear before test

        text1 = "What time is check-in?"
        text2 = "What time is check-in?"  # Identical

        embedding = [0.1, 0.2, 0.3]
        cache.set_embedding(text1, embedding)

        retrieved = cache.get_embedding(text2)
        assert retrieved == embedding

    def test_cache_size(self):
        """Test cache size tracking."""
        cache = EmbeddingCache()
        cache.clear()  # Clear before test

        # Add embeddings
        cache.set_embedding("text1", [0.1])
        cache.set_embedding("text2", [0.2])

        assert cache.size() == 2


class TestToolResultCache:
    """Test ToolResultCache."""

    def test_set_and_get_tool_result(self):
        """Test setting and getting tool results using cache keys."""
        cache = ToolResultCache()
        cache.clear()  # Clear before test

        key = "property:prop_001"
        result = {
            "id": "prop_001",
            "name": "Test Hotel",
            "check_in_time": "3:00 PM",
        }

        cache.set(key, result)
        retrieved = cache.get(key)

        assert retrieved == result

    def test_different_keys_no_match(self):
        """Test that different keys don't match."""
        cache = ToolResultCache()
        cache.clear()  # Clear before test

        cache.set("property:prop_001", {"name": "Hotel A"})
        retrieved = cache.get("property:prop_002")

        assert retrieved is None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = ToolResultCache()
        cache.clear()  # Clear before test

        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})

        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0


class TestResponseCache:
    """Test ResponseCache."""

    def test_set_and_get_response(self):
        """Test setting and getting cached responses."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        message = "What time is check-in?"
        property_id = "prop_001"
        reservation_id = "res_001"

        response = {
            "response_text": "Check-in is at 3:00 PM",
            "response_type": "template",
            "confidence_score": 0.9,
            "metadata": {
                "execution_time_ms": 450.5,
                "pii_detected": False,
                "templates_found": 3,
            },
        }

        cache.set_response(message, property_id, reservation_id, response)
        retrieved = cache.get_response(message, property_id, reservation_id)

        assert retrieved == response

    def test_different_message_no_match(self):
        """Test that different messages don't match."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        response = {"response_text": "Check-in is at 3:00 PM"}

        cache.set_response("What time is check-in?", "prop_001", None, response)
        retrieved = cache.get_response("What time is check-out?", "prop_001", None)

        assert retrieved is None

    def test_different_property_no_match(self):
        """Test that different property IDs don't match."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        response = {"response_text": "Check-in is at 3:00 PM"}

        cache.set_response("What time is check-in?", "prop_001", None, response)
        retrieved = cache.get_response("What time is check-in?", "prop_002", None)

        assert retrieved is None

    def test_different_reservation_no_match(self):
        """Test that different reservation IDs don't match."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        response = {"response_text": "Your reservation details"}

        cache.set_response("Show my reservation", "prop_001", "res_001", response)
        retrieved = cache.get_response("Show my reservation", "prop_001", "res_002")

        assert retrieved is None

    def test_none_reservation_matches(self):
        """Test that None reservation ID is handled correctly."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        response = {"response_text": "General information"}

        cache.set_response("General question", "prop_001", None, response)
        retrieved = cache.get_response("General question", "prop_001", None)

        assert retrieved == response

    def test_cache_size(self):
        """Test cache size tracking."""
        cache = ResponseCache()
        cache.clear()  # Clear before test

        # Add responses
        cache.set_response("q1", "p1", None, {"response": "a1"})
        cache.set_response("q2", "p1", None, {"response": "a2"})

        assert cache.size() == 2
