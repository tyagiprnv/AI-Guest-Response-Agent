"""
Agent state schema for LangGraph.
"""
from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    """State schema for the guest response agent."""

    # Input
    guest_message: str
    property_id: str
    reservation_id: str | None

    # Guardrails
    pii_detected: bool
    redacted_message: str
    topic_filter_result: Dict[str, Any]

    # Tool results
    retrieved_templates: List[Dict[str, Any]]
    property_details: Dict[str, Any] | None
    reservation_details: Dict[str, Any] | None

    # Generation
    response_type: str  # "template" | "custom" | "no_response"
    final_response: str
    confidence_score: float

    # Metadata
    execution_time_ms: float
    tokens_used: Dict[str, int]
    cost_usd: float
    error: str | None
