"""Integration tests for the complete agent workflow."""

import pytest
from src.agent.graph import run_agent


@pytest.mark.asyncio
class TestAgentWorkflow:
    """Test complete agent workflows end-to-end."""

    async def test_simple_query_template_response(self):
        """Test that a simple query returns a template response."""
        result = await run_agent(
            guest_message="What time is check-in?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Assertions
        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]
        assert result["confidence_score"] >= 0.0
        assert result["confidence_score"] <= 1.0
        assert "metadata" in result
        assert result["metadata"]["execution_time_ms"] > 0

    async def test_query_with_property_and_reservation(self):
        """Test query that uses both property and reservation data."""
        result = await run_agent(
            guest_message="What's my check-in time and room type?",
            property_id="prop_001",
            reservation_id="res_001",
        )

        # Check response
        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]
        assert "metadata" in result

    async def test_pii_blocked_query(self):
        """Test that queries with highly sensitive PII are blocked."""
        result = await run_agent(
            guest_message="My SSN is 123-45-6789",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should be rejected by PII guardrail
        assert result["response_type"] == "no_response"
        # Check that the response is a polite decline
        response_lower = result["response_text"].lower()
        assert any(word in response_lower for word in ["cannot", "unable", "privacy", "apologize"])

    async def test_pii_redaction_email(self):
        """Test that email PII is redacted but message is processed."""
        result = await run_agent(
            guest_message="My email is test@example.com. What time is check-in?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Email should be redacted but message still processed
        assert result["response_text"] != ""
        assert result["metadata"]["pii_detected"] is True

    async def test_restricted_topic_query(self):
        """Test that restricted topics are rejected."""
        result = await run_agent(
            guest_message="Can you help me sue my landlord?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should be rejected by topic filter
        assert result["response_type"] == "no_response"

    async def test_allowed_topic_query(self):
        """Test that allowed topics are processed."""
        result = await run_agent(
            guest_message="Do you have a swimming pool?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should be processed
        assert result["response_type"] in ["template", "custom"]
        assert result["response_text"] != ""

    async def test_multiple_queries_parallel(self):
        """Test that multiple queries can be processed in parallel."""
        import asyncio

        queries = [
            "What time is check-in?",
            "Is parking available?",
            "What are the WiFi details?",
        ]

        tasks = [
            run_agent(
                guest_message=query,
                property_id="prop_001",
                reservation_id=None,
            )
            for query in queries
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert result["response_text"] != ""
            assert result["response_type"] in ["template", "custom"]

    async def test_template_retrieval_high_confidence(self):
        """Test that template retrieval works for common queries."""
        result = await run_agent(
            guest_message="What is the check-in time?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should find templates
        assert result["metadata"]["templates_found"] > 0
        # Likely to be a template response for common query
        if result["response_type"] == "template":
            assert result["confidence_score"] > 0.65

    async def test_graceful_degradation_no_property(self):
        """Test that agent handles missing property gracefully."""
        result = await run_agent(
            guest_message="What time is check-in?",
            property_id="nonexistent_property",
            reservation_id=None,
        )

        # Should still return a response (graceful degradation)
        assert result["response_text"] != ""
        # Response type should be custom or error
        assert result["response_type"] in ["template", "custom", "error"]

    async def test_graceful_degradation_no_reservation(self):
        """Test that agent handles missing reservation gracefully."""
        result = await run_agent(
            guest_message="What's my room type?",
            property_id="prop_001",
            reservation_id="nonexistent_reservation",
        )

        # Should still return a response
        assert result["response_text"] != ""

    async def test_response_metadata_complete(self):
        """Test that metadata is properly tracked."""
        result = await run_agent(
            guest_message="What time is check-out?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Check metadata structure
        metadata = result["metadata"]
        assert "execution_time_ms" in metadata
        assert metadata["execution_time_ms"] > 0
        assert "pii_detected" in metadata
        assert "templates_found" in metadata
        assert metadata["templates_found"] >= 0

    async def test_custom_response_generation(self):
        """Test that custom responses are generated when no template matches."""
        # Use an unusual query that's unlikely to have a template
        result = await run_agent(
            guest_message="Can you tell me about the history of your property?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should generate a response
        assert result["response_text"] != ""
        # May be custom or template depending on templates available
        assert result["response_type"] in ["template", "custom"]

    async def test_parking_query(self):
        """Test parking-related queries."""
        result = await run_agent(
            guest_message="Is parking available?",
            property_id="prop_001",
            reservation_id=None,
        )

        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]

    async def test_amenities_query(self):
        """Test amenities-related queries."""
        result = await run_agent(
            guest_message="What amenities do you offer?",
            property_id="prop_001",
            reservation_id=None,
        )

        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]

    async def test_policies_query(self):
        """Test policy-related queries."""
        result = await run_agent(
            guest_message="What is your cancellation policy?",
            property_id="prop_001",
            reservation_id=None,
        )

        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]

    async def test_special_requests_query(self):
        """Test special requests queries."""
        result = await run_agent(
            guest_message="Can I request early check-in?",
            property_id="prop_001",
            reservation_id=None,
        )

        assert result["response_text"] != ""
        assert result["response_type"] in ["template", "custom"]

    async def test_confidence_score_range(self):
        """Test that confidence scores are in valid range."""
        queries = [
            "What time is check-in?",
            "Is WiFi available?",
            "Tell me about your property",
        ]

        for query in queries:
            result = await run_agent(
                guest_message=query,
                property_id="prop_001",
                reservation_id=None,
            )

            # Confidence score should be between 0 and 1
            assert result["confidence_score"] >= 0.0
            assert result["confidence_score"] <= 1.0

    async def test_error_handling(self):
        """Test that errors are handled gracefully."""
        # Test with empty message (should be caught by API validation in real usage)
        # But the agent itself should handle it
        result = await run_agent(
            guest_message="",
            property_id="prop_001",
            reservation_id=None,
        )

        # Should return some response, even if error
        assert "response_text" in result
        assert "response_type" in result

    async def test_long_message_handling(self):
        """Test handling of longer messages."""
        long_message = "What time is check-in? " * 20
        result = await run_agent(
            guest_message=long_message,
            property_id="prop_001",
            reservation_id=None,
        )

        assert result["response_text"] != ""

    async def test_response_type_values(self):
        """Test that response_type has valid values."""
        result = await run_agent(
            guest_message="What time is check-in?",
            property_id="prop_001",
            reservation_id=None,
        )

        # Valid response types
        valid_types = ["template", "custom", "no_response", "error"]
        assert result["response_type"] in valid_types
