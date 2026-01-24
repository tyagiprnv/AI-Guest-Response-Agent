"""
LangGraph agent nodes.
"""
import asyncio
import json
from time import time
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from src.agent.prompts import (
    CUSTOM_RESPONSE_PROMPT,
    NO_RESPONSE_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)
from src.agent.state import AgentState
from src.config.settings import get_settings
from src.guardrails.pii_redaction import detect_and_redact_pii, should_block_pii
from src.guardrails.topic_filter import check_topic_restriction
from src.monitoring.logging import get_logger
from src.monitoring.metrics import response_type_count, tokens_used, cost_usd
from src.tools.property_details import get_property_info
from src.tools.reservation_details import get_reservation_info
from src.tools.template_retrieval import retrieve_templates

logger = get_logger(__name__)


async def apply_guardrails(state: AgentState) -> Dict[str, Any]:
    """Apply safety guardrails to the guest message."""
    message = state["guest_message"]

    # Check for sensitive PII that should block request
    if should_block_pii(message):
        return {
            "pii_detected": True,
            "redacted_message": message,
            "topic_filter_result": {
                "allowed": False,
                "reason": "Sensitive PII detected",
                "topic": "blocked",
            },
        }

    # Detect and redact PII
    redacted_message, has_pii = await detect_and_redact_pii(message)

    # Check topic restrictions
    topic_result = await check_topic_restriction(redacted_message)

    logger.info(
        f"Guardrails applied - PII: {has_pii}, Topic allowed: {topic_result['allowed']}"
    )

    return {
        "pii_detected": has_pii,
        "redacted_message": redacted_message,
        "topic_filter_result": topic_result,
    }


async def execute_tools(state: AgentState) -> Dict[str, Any]:
    """Execute all tools in parallel."""
    start_time = time()

    # Execute tools in parallel
    templates_task = retrieve_templates(state["redacted_message"])
    property_task = get_property_info(state["property_id"])
    reservation_task = get_reservation_info(state.get("reservation_id"))

    templates, property_info, reservation_info = await asyncio.gather(
        templates_task, property_task, reservation_task
    )

    execution_time = (time() - start_time) * 1000

    logger.info(
        f"Tools executed in {execution_time:.0f}ms - "
        f"Templates: {len(templates)}, Property: {property_info is not None}, "
        f"Reservation: {reservation_info is not None}"
    )

    return {
        "retrieved_templates": templates,
        "property_details": property_info,
        "reservation_details": reservation_info,
    }


async def generate_response(state: AgentState) -> Dict[str, Any]:
    """Generate the final response."""
    settings = get_settings()

    # Check if request was blocked by guardrails
    if not state["topic_filter_result"]["allowed"]:
        return await generate_no_response(state)

    # Check if we have good template matches
    templates = state.get("retrieved_templates", [])
    has_good_templates = templates and templates[0]["score"] >= 0.75

    if has_good_templates:
        return await generate_template_response(state)
    else:
        return await generate_custom_response(state)


async def generate_template_response(state: AgentState) -> Dict[str, Any]:
    """Generate response using templates."""
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=settings.openai_api_key,
    )

    # Format templates
    templates_text = "\n\n".join([
        f"Template {i+1} (similarity: {t['score']:.3f}):\n"
        f"Category: {t['payload']['category']}\n"
        f"Text: {t['payload']['text']}"
        for i, t in enumerate(state["retrieved_templates"][:3])
    ])

    # Format property and reservation info
    property_info = json.dumps(state.get("property_details"), indent=2) if state.get("property_details") else "Not available"
    reservation_info = json.dumps(state.get("reservation_details"), indent=2) if state.get("reservation_details") else "Not available"

    prompt = RESPONSE_GENERATION_PROMPT.format(
        guest_message=state["redacted_message"],
        templates=templates_text,
        property_info=property_info,
        reservation_info=reservation_info,
    )

    response = await llm.ainvoke(prompt)

    # Parse JSON response
    try:
        result = json.loads(response.content)

        # Update metrics
        response_type_count.labels(response_type="template").inc()
        if hasattr(response, 'usage_metadata'):
            tokens_used.labels(token_type="prompt").inc(response.usage_metadata.get('input_tokens', 0))
            tokens_used.labels(token_type="completion").inc(response.usage_metadata.get('output_tokens', 0))

        return {
            "response_type": "template",
            "final_response": result["response_text"],
            "confidence_score": result.get("confidence_score", 0.9),
        }
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON")
        return {
            "response_type": "template",
            "final_response": response.content,
            "confidence_score": 0.7,
        }


async def generate_custom_response(state: AgentState) -> Dict[str, Any]:
    """Generate custom response without templates."""
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=settings.openai_api_key,
    )

    property_info = json.dumps(state.get("property_details"), indent=2) if state.get("property_details") else "Not available"
    reservation_info = json.dumps(state.get("reservation_details"), indent=2) if state.get("reservation_details") else "Not available"

    prompt = CUSTOM_RESPONSE_PROMPT.format(
        guest_message=state["redacted_message"],
        property_info=property_info,
        reservation_info=reservation_info,
    )

    response = await llm.ainvoke(prompt)

    try:
        result = json.loads(response.content)
        response_text = result["response_text"]
    except json.JSONDecodeError:
        response_text = response.content

    # Update metrics
    response_type_count.labels(response_type="custom").inc()
    if hasattr(response, 'usage_metadata'):
        tokens_used.labels(token_type="prompt").inc(response.usage_metadata.get('input_tokens', 0))
        tokens_used.labels(token_type="completion").inc(response.usage_metadata.get('output_tokens', 0))

    return {
        "response_type": "custom",
        "final_response": response_text,
        "confidence_score": 0.7,
    }


async def generate_no_response(state: AgentState) -> Dict[str, Any]:
    """Generate polite decline response."""
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=settings.openai_api_key,
    )

    reason = state["topic_filter_result"]["reason"]
    prompt = NO_RESPONSE_PROMPT.format(reason=reason)

    response = await llm.ainvoke(prompt)

    try:
        result = json.loads(response.content)
        response_text = result["response_text"]
    except json.JSONDecodeError:
        response_text = "I apologize, but I'm unable to assist with this type of request. Please contact the property directly for further assistance."

    # Update metrics
    response_type_count.labels(response_type="no_response").inc()

    return {
        "response_type": "no_response",
        "final_response": response_text,
        "confidence_score": 1.0,
    }


def should_continue(state: AgentState) -> str:
    """Determine if workflow should continue or reject."""
    if not state["topic_filter_result"]["allowed"]:
        return "reject"
    return "continue"
