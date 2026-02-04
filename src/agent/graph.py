"""
LangGraph agent workflow definition.
"""
from functools import lru_cache
from time import time
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from src.agent.nodes import (
    apply_guardrails,
    execute_tools,
    generate_response,
    should_continue,
)
from src.agent.state import AgentState
from src.monitoring.logging import get_logger
from src.monitoring.metrics import request_count, request_duration

logger = get_logger(__name__)


def create_agent_graph() -> StateGraph:
    """Create the agent workflow graph."""

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("apply_guardrails", apply_guardrails)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("generate_response", generate_response)

    # Set entry point
    workflow.set_entry_point("apply_guardrails")

    # Add conditional edges
    workflow.add_conditional_edges(
        "apply_guardrails",
        should_continue,
        {
            "continue": "execute_tools",
            "reject": "generate_response",
        },
    )

    # Add edges
    workflow.add_edge("execute_tools", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


async def run_agent(
    guest_message: str,
    property_id: str,
    reservation_id: str | None = None,
) -> Dict[str, Any]:
    """
    Run the agent workflow.

    Args:
        guest_message: The guest's message/query
        property_id: Property ID
        reservation_id: Optional reservation ID

    Returns:
        Dict with response and metadata
    """
    start_time = time()

    # Initialize state
    initial_state: AgentState = {
        "guest_message": guest_message,
        "property_id": property_id,
        "reservation_id": reservation_id,
        # Initialize other fields
        "pii_detected": False,
        "redacted_message": guest_message,
        "topic_filter_result": {},
        "retrieved_templates": [],
        "property_details": None,
        "reservation_details": None,
        "response_type": "",
        "final_response": "",
        "confidence_score": 0.0,
        "execution_time_ms": 0.0,
        "tokens_used": {},
        "cost_usd": 0.0,
        "error": None,
    }

    try:
        # Create and run graph
        graph = create_agent_graph()
        final_state = await graph.ainvoke(initial_state)

        # Calculate execution time
        execution_time = (time() - start_time) * 1000

        # Update metrics
        request_count.labels(
            status="success",
            response_type=final_state.get("response_type", "unknown")
        ).inc()
        request_duration.observe(execution_time / 1000)

        # Build response
        response = {
            "response_text": final_state.get("final_response", ""),
            "response_type": final_state.get("response_type", "unknown"),
            "confidence_score": final_state.get("confidence_score", 0.0),
            "metadata": {
                "execution_time_ms": execution_time,
                "pii_detected": final_state.get("pii_detected", False),
                "templates_found": len(final_state.get("retrieved_templates", [])),
            },
        }

        logger.info(
            f"Agent completed successfully in {execution_time:.0f}ms - "
            f"Type: {response['response_type']}"
        )

        return response

    except Exception as e:
        execution_time = (time() - start_time) * 1000

        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)

        # Update metrics
        request_count.labels(status="error", response_type="error").inc()

        return {
            "response_text": "I apologize, but I encountered an error processing your request. Please try again or contact the property directly.",
            "response_type": "error",
            "confidence_score": 0.0,
            "metadata": {
                "execution_time_ms": execution_time,
                "error": str(e),
            },
        }
