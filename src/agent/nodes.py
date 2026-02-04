"""
LangGraph agent nodes.
"""
import asyncio
import json
from datetime import datetime, date
from time import time
from typing import Any, Dict

from langchain_groq import ChatGroq

from src.agent.prompts import (
    CUSTOM_RESPONSE_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)
from src.agent.state import AgentState
from src.config.settings import get_settings
from src.guardrails.pii_redaction import detect_and_redact_pii, should_block_pii
from src.guardrails.topic_filter import check_topic_restriction
from src.monitoring.cost import calculate_llm_cost
from src.monitoring.logging import get_logger
from src.monitoring.metrics import response_type_count, tokens_used, cost_usd, direct_substitution_count
from src.tools.property_details import get_property_info
from src.tools.reservation_details import get_reservation_info
from src.tools.template_retrieval import retrieve_templates
from src.tools.template_substitution import build_context, can_use_direct_substitution

logger = get_logger(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def apply_guardrails(state: AgentState) -> Dict[str, Any]:
    """Apply safety guardrails to the guest message."""
    from src.guardrails.topic_filter import is_safe_query, topic_filter_path, check_topic_restriction

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

    # Detect and redact PII (synchronous call)
    redacted_message, has_pii = detect_and_redact_pii(message)

    # Fast-path topic check: Skip LLM for obviously safe queries
    topic_result = None
    if is_safe_query(redacted_message):
        logger.debug(f"Topic filter fast-path: query is safe - {redacted_message[:50]}...")
        topic_filter_path.labels(path="fast_path").inc()
        topic_result = {
            "allowed": True,
            "reason": "Query matches safe patterns",
            "topic": "general",
        }
    # Note: For non-fast-path queries, topic checking happens in generate_response (parallel with response generation)

    logger.info(
        f"Guardrails applied - PII: {has_pii}, Fast-path topic check: {topic_result is not None}"
    )

    return {
        "pii_detected": has_pii,
        "redacted_message": redacted_message,
        "topic_filter_result": topic_result,  # None if needs LLM check, dict if fast-path passed
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

    # Validate reservation belongs to property (security check)
    if reservation_info and reservation_info.get("property_id") != state["property_id"]:
        logger.warning(
            f"Reservation {state.get('reservation_id')} does not belong to property {state['property_id']} "
            f"(belongs to {reservation_info.get('property_id')}). Clearing reservation data."
        )
        reservation_info = None

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
    """Generate the final response with parallel topic checking for non-fast-path queries."""
    from src.guardrails.topic_filter import check_topic_restriction

    settings = get_settings()

    # Check if request was blocked by fast-path topic filter or PII
    topic_result = state.get("topic_filter_result")
    if topic_result is not None and not topic_result["allowed"]:
        return await generate_no_response(state)

    # For queries that didn't match fast-path, run topic check in parallel with response generation
    needs_topic_check = topic_result is None

    # Check if we have good template matches
    templates = state.get("retrieved_templates", [])
    has_good_templates = templates and templates[0]["score"] >= settings.retrieval_similarity_threshold

    # Try direct substitution for very high confidence matches (only if topic already checked)
    if has_good_templates and settings.direct_substitution_enabled and not needs_topic_check:
        best_template = templates[0]
        if best_template["score"] >= settings.direct_substitution_threshold:
            result = await generate_direct_template_response(state)
            if result is not None:
                return result
            # Fall through to LLM-based response

    # If topic check needed, run in parallel with response generation
    if needs_topic_check:
        # Start both tasks in parallel
        topic_task = asyncio.create_task(check_topic_restriction(state["redacted_message"]))

        if has_good_templates:
            response_task = asyncio.create_task(generate_template_response(state))
        else:
            response_task = asyncio.create_task(generate_custom_response(state))

        # Wait for topic filter first
        topic_result = await topic_task

        # If topic is blocked, cancel response generation and return rejection
        if not topic_result["allowed"]:
            if not response_task.done():
                response_task.cancel()
                try:
                    await response_task
                except asyncio.CancelledError:
                    logger.info("Cancelled response generation due to topic restriction")
                    pass

            # Update state with topic filter result for generate_no_response
            state["topic_filter_result"] = topic_result
            return await generate_no_response(state)

        # Topic allowed - wait for and return the response
        return await response_task

    # Topic already checked (fast-path), just generate response
    if has_good_templates:
        return await generate_template_response(state)
    else:
        return await generate_custom_response(state)


async def generate_direct_template_response(state: AgentState) -> Dict[str, Any] | None:
    """
    Generate response using direct template substitution (no LLM call).

    Returns None if substitution fails, allowing fallback to LLM-based generation.
    """
    settings = get_settings()
    templates = state.get("retrieved_templates", [])

    if not templates:
        direct_substitution_count.labels(status="fallback_low_score").inc()
        return None

    best_template = templates[0]

    # Build context from property and reservation data
    context = build_context(
        state.get("property_details"),
        state.get("reservation_details")
    )

    # Check if we can use direct substitution
    can_substitute, substituted_text, unfilled = can_use_direct_substitution(
        best_template,
        context,
        score_threshold=settings.direct_substitution_threshold
    )

    if not can_substitute:
        if unfilled:
            logger.info(f"Direct substitution failed - unfilled placeholders: {unfilled}")
            direct_substitution_count.labels(status="fallback_unfilled").inc()
        else:
            logger.info(f"Direct substitution failed - score below threshold")
            direct_substitution_count.labels(status="fallback_low_score").inc()
        return None

    logger.info(
        f"Direct template substitution successful - "
        f"score: {best_template['score']:.3f}, template: {best_template['payload'].get('id', 'unknown')}"
    )

    # Update metrics
    direct_substitution_count.labels(status="success").inc()
    response_type_count.labels(response_type="direct_template").inc()

    return {
        "response_type": "direct_template",
        "final_response": substituted_text,
        "confidence_score": best_template["score"],
    }


async def generate_template_response(state: AgentState) -> Dict[str, Any]:
    """Generate response using templates."""
    settings = get_settings()
    llm = ChatGroq(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.groq_api_key,
        max_tokens=settings.llm_max_tokens,
    )

    # Format templates
    templates_text = "\n\n".join([
        f"Template {i+1} (similarity: {t['score']:.3f}):\n"
        f"Category: {t['payload']['category']}\n"
        f"Text: {t['payload']['text']}"
        for i, t in enumerate(state["retrieved_templates"][:3])
    ])

    # Format property and reservation info
    property_info = json.dumps(state.get("property_details"), indent=2, default=json_serial) if state.get("property_details") else "Not available"
    reservation_info = json.dumps(state.get("reservation_details"), indent=2, default=json_serial) if state.get("reservation_details") else "Not available"

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
            input_tokens = response.usage_metadata.get('input_tokens', 0)
            output_tokens = response.usage_metadata.get('output_tokens', 0)

            tokens_used.labels(token_type="prompt").inc(input_tokens)
            tokens_used.labels(token_type="completion").inc(output_tokens)

            # Calculate and track cost
            settings = get_settings()
            if settings.enable_cost_tracking:
                cost = calculate_llm_cost(input_tokens, output_tokens, settings.llm_model)
                cost_usd.labels(response_type="template", model=settings.llm_model).inc(cost)

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
    llm = ChatGroq(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.groq_api_key,
        max_tokens=settings.llm_max_tokens,
    )

    property_info = json.dumps(state.get("property_details"), indent=2, default=json_serial) if state.get("property_details") else "Not available"
    reservation_info = json.dumps(state.get("reservation_details"), indent=2, default=json_serial) if state.get("reservation_details") else "Not available"

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
        input_tokens = response.usage_metadata.get('input_tokens', 0)
        output_tokens = response.usage_metadata.get('output_tokens', 0)

        tokens_used.labels(token_type="prompt").inc(input_tokens)
        tokens_used.labels(token_type="completion").inc(output_tokens)

        # Calculate and track cost
        settings = get_settings()
        if settings.enable_cost_tracking:
            cost = calculate_llm_cost(input_tokens, output_tokens, settings.llm_model)
            cost_usd.labels(response_type="custom", model=settings.llm_model).inc(cost)

    return {
        "response_type": "custom",
        "final_response": response_text,
        "confidence_score": 0.7,
    }


async def generate_no_response(state: AgentState) -> Dict[str, Any]:
    """Generate polite decline response without LLM call."""
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
    topic_result = state.get("topic_filter_result")
    # None means passed fast-path check (allowed)
    # Dict with "allowed": False means blocked
    if topic_result is not None and not topic_result.get("allowed", True):
        return "reject"
    return "continue"
