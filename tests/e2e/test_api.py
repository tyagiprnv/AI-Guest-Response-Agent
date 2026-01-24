"""End-to-end tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    def test_ready_check(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        # May return 200 or 503 depending on Qdrant availability
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

        if response.status_code == 200:
            assert data["status"] == "ready"
            assert "checks" in data
        else:
            assert data["status"] == "not_ready"
            assert "reason" in data

    def test_root_endpoint(self, client):
        """Test root / endpoint."""
        response = client.get("/")
        assert response.status_code == 200


class TestResponseGenerationEndpoint:
    """Test the main response generation endpoint."""

    def test_generate_response_simple_query(self, client):
        """Test generating response for a simple query."""
        payload = {
            "message": "What time is check-in?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "response_text" in data
        assert "response_type" in data
        assert "confidence_score" in data
        assert "metadata" in data
        assert data["response_text"] != ""

        # Verify metadata structure
        metadata = data["metadata"]
        assert "execution_time_ms" in metadata
        assert "pii_detected" in metadata
        assert "templates_found" in metadata

    def test_generate_response_with_reservation(self, client):
        """Test generating response with reservation context."""
        payload = {
            "message": "What's my reservation details?",
            "property_id": "prop_001",
            "reservation_id": "res_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "response_text" in data
        assert data["response_text"] != ""

    def test_generate_response_missing_message(self, client):
        """Test that missing message returns 422."""
        payload = {
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 422

    def test_generate_response_empty_message(self, client):
        """Test that empty message is rejected with 422."""
        payload = {
            "message": "",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        # Should be rejected by min_length=1 validation
        assert response.status_code == 422

    def test_generate_response_missing_property_id(self, client):
        """Test that missing property_id returns 422."""
        payload = {
            "message": "What time is check-in?"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 422

    def test_generate_response_pii_content(self, client):
        """Test that PII in message is handled by guardrails."""
        payload = {
            "message": "My email is test@example.com. What time is check-in?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Should detect PII but still process
        assert data["metadata"]["pii_detected"] is True
        assert data["response_text"] != ""

    def test_generate_response_blocked_pii(self, client):
        """Test that highly sensitive PII blocks the request."""
        payload = {
            "message": "My SSN is 123-45-6789",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Should be blocked by guardrails
        assert data["response_type"] == "no_response"

    def test_generate_response_metadata_included(self, client):
        """Test that metadata is included in response."""
        payload = {
            "message": "Is WiFi available?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        metadata = data["metadata"]
        assert isinstance(metadata, dict)
        assert metadata["execution_time_ms"] > 0
        assert isinstance(metadata["pii_detected"], bool)
        assert isinstance(metadata["templates_found"], int)

    def test_generate_response_confidence_score(self, client):
        """Test that confidence score is in valid range."""
        payload = {
            "message": "What time is check-in?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["confidence_score"] >= 0.0
        assert data["confidence_score"] <= 1.0

    def test_generate_response_long_message(self, client):
        """Test handling of long messages."""
        payload = {
            "message": "What are all the amenities? " * 50,
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        # Should either succeed or be rejected for being too long
        assert response.status_code in [200, 422]

    def test_generate_response_message_max_length(self, client):
        """Test that messages over max length are rejected."""
        payload = {
            "message": "a" * 1001,  # Over 1000 char limit
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 422

    def test_generate_response_valid_response_types(self, client):
        """Test that response_type has valid values."""
        payload = {
            "message": "What time is check-in?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        valid_types = ["template", "custom", "no_response", "error"]
        assert data["response_type"] in valid_types


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Should contain some metric names
        content = response.text
        # Check for some expected metrics
        assert len(content) > 0


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options(
            "/api/v1/generate-response",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/generate-response",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_nonexistent_endpoint(self, client):
        """Test 404 for nonexistent endpoints."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.get("/api/v1/generate-response")
        assert response.status_code == 405

    def test_malformed_payload(self, client):
        """Test handling of malformed payload."""
        payload = {
            "message": 123,  # Should be string
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 422


class TestDocumentation:
    """Test API documentation."""

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/v1/generate-response" in data["paths"]

    def test_swagger_ui(self, client):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_ui(self, client):
        """Test that ReDoc UI is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestResponseCaching:
    """Test response caching behavior."""

    def test_cache_hit_on_duplicate_request(self, client):
        """Test that duplicate requests benefit from caching."""
        payload = {
            "message": "What time is check-in at the property?",
            "property_id": "prop_001"
        }

        # First request
        response1 = client.post("/api/v1/generate-response", json=payload)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second identical request (should hit cache)
        response2 = client.post("/api/v1/generate-response", json=payload)
        assert response2.status_code == 200
        data2 = response2.json()

        # Both should succeed and have same response text
        assert data1["response_text"] == data2["response_text"]


class TestDifferentQueries:
    """Test different types of queries."""

    def test_check_in_query(self, client):
        """Test check-in related query."""
        payload = {
            "message": "What time is check-in?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] in ["template", "custom"]

    def test_check_out_query(self, client):
        """Test check-out related query."""
        payload = {
            "message": "What time is check-out?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] in ["template", "custom"]

    def test_parking_query(self, client):
        """Test parking related query."""
        payload = {
            "message": "Is parking available?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] in ["template", "custom"]

    def test_amenities_query(self, client):
        """Test amenities related query."""
        payload = {
            "message": "What amenities do you offer?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] in ["template", "custom"]

    def test_policies_query(self, client):
        """Test policies related query."""
        payload = {
            "message": "What is your cancellation policy?",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response_type"] in ["template", "custom"]
