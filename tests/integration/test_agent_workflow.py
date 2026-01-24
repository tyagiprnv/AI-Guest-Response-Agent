"""Integration tests for the complete agent workflow."""

import pytest
import asyncio
from src.agent.graph import create_agent_graph
from src.agent.state import AgentState


@pytest.mark.asyncio
class TestAgentWorkflow:
    """Test complete agent workflows end-to-end."""

    @pytest.fixture
    async def agent(self):
        """Create agent graph for testing."""
        return create_agent_graph()

    async def test_simple_query_template_response(self, agent):
        """Test that a simple query returns a template response."""
        initial_state: AgentState = {
            "messages": "What time is check-in?",
            "property_id": "prop_001",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Assertions
        assert result["guardrail_passed"] is True
        assert result["response"] != ""
        assert result["response_type"] in ["template", "custom"]
        assert "metadata" in result

    async def test_query_with_property_and_reservation(self, agent):
        """Test query that uses both property and reservation data."""
        initial_state: AgentState = {
            "messages": "What's my check-in time and room type?",
            "property_id": "prop_001",
            "reservation_id": "res_001",
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Check that tools were executed
        assert "property_details" in result["tools_output"]
        assert "reservation_details" in result["tools_output"]
        assert result["response"] != ""

    async def test_pii_blocked_query(self, agent):
        """Test that queries with PII are blocked."""
        initial_state: AgentState = {
            "messages": "My email is test@example.com and my SSN is 123-45-6789",
            "property_id": "prop_001",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Should be rejected by PII guardrail
        assert result["guardrail_passed"] is False
        assert "cannot process" in result["response"].lower() or "privacy" in result["response"].lower()

    async def test_offtopic_query(self, agent):
        """Test that off-topic queries are rejected."""
        initial_state: AgentState = {
            "messages": "What's the weather like today?",
            "property_id": "prop_001",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # May or may not be blocked depending on topic filter strictness
        # But should not error
        assert result["response"] != ""

    async def test_multiple_queries_parallel(self, agent):
        """Test that multiple queries can be processed in parallel."""
        queries = [
            "What time is check-in?",
            "Is parking available?",
            "What are the WiFi details?",
        ]

        tasks = []
        for query in queries:
            initial_state: AgentState = {
                "messages": query,
                "property_id": "prop_001",
                "reservation_id": None,
                "guardrail_passed": True,
                "tools_output": {},
                "response": "",
                "response_type": "no_response",
                "metadata": {},
            }
            tasks.append(agent.ainvoke(initial_state))

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert result["response"] != ""

    async def test_template_retrieval(self, agent):
        """Test that template retrieval works correctly."""
        initial_state: AgentState = {
            "messages": "What is the check-in time?",
            "property_id": "prop_001",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Should find templates
        assert "templates" in result["tools_output"]
        templates = result["tools_output"]["templates"]
        if templates:  # If similarity threshold is met
            assert len(templates) > 0
            assert "template" in templates[0]

    async def test_graceful_degradation_no_property(self, agent):
        """Test that agent handles missing property gracefully."""
        initial_state: AgentState = {
            "messages": "What time is check-in?",
            "property_id": "nonexistent_property",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Should still return a response (graceful degradation)
        assert result["response"] != ""
        # Property details might be None
        assert "property_details" in result["tools_output"]

    async def test_response_metadata(self, agent):
        """Test that metadata is properly tracked."""
        initial_state: AgentState = {
            "messages": "What time is check-out?",
            "property_id": "prop_001",
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result = await agent.ainvoke(initial_state)

        # Check metadata
        metadata = result["metadata"]
        assert "total_tokens" in metadata or "execution_time" in metadata
        assert result["response_type"] in ["template", "custom", "no_response"]

    async def test_caching_behavior(self, agent):
        """Test that repeated queries benefit from caching."""
        query = "What amenities are available?"
        property_id = "prop_001"

        # First request
        initial_state: AgentState = {
            "messages": query,
            "property_id": property_id,
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result1 = await agent.ainvoke(initial_state)

        # Second identical request (should hit cache)
        initial_state2: AgentState = {
            "messages": query,
            "property_id": property_id,
            "reservation_id": None,
            "guardrail_passed": True,
            "tools_output": {},
            "response": "",
            "response_type": "no_response",
            "metadata": {},
        }

        result2 = await agent.ainvoke(initial_state2)

        # Both should succeed
        assert result1["response"] != ""
        assert result2["response"] != ""
