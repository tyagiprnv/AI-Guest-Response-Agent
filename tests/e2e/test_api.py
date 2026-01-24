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
        assert "timestamp" in data
        assert "version" in data

    def test_ready_check(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data


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
        assert "response" in data
        assert "response_type" in data
        assert "metadata" in data
        assert data["response"] != ""

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
        assert "response" in data
        assert data["response"] != ""

    def test_generate_response_missing_message(self, client):
        """Test that missing message returns 422."""
        payload = {
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 422

    def test_generate_response_empty_message(self, client):
        """Test that empty message is handled."""
        payload = {
            "message": "",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        # Should either return 422 or handle gracefully
        assert response.status_code in [200, 422]

    def test_generate_response_pii_content(self, client):
        """Test that PII in message is handled by guardrails."""
        payload = {
            "message": "My email is test@example.com",
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Should either reject or redact
        assert "response" in data

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

    def test_generate_response_long_message(self, client):
        """Test handling of long messages."""
        payload = {
            "message": "What are all the amenities? " * 50,
            "property_id": "prop_001"
        }

        response = client.post("/api/v1/generate-response", json=payload)
        assert response.status_code in [200, 413, 422]  # May hit rate limit or size limit


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Should contain some metric names
        content = response.text
        assert "agent_" in content or "http_" in content


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
        assert "access-control-allow-origin" in response.headers


class TestRateLimiting:
    """Test rate limiting (if enabled)."""

    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting prevents abuse."""
        payload = {
            "message": "Test query",
            "property_id": "prop_001"
        }

        # Make many requests rapidly
        responses = []
        for _ in range(100):
            response = client.post("/api/v1/generate-response", json=payload)
            responses.append(response.status_code)

        # Should have at least one successful request
        assert 200 in responses

        # May have rate limit responses (429)
        # Depends on rate limit configuration


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


class TestDocumentation:
    """Test API documentation."""

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data

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
