"""
Topic filter to restrict certain types of queries.
"""
import json
import re
from typing import Any, Dict

from langchain_deepseek import ChatDeepSeek

from src.config.settings import get_settings
from src.monitoring.logging import get_logger
from src.monitoring.metrics import guardrail_triggered

logger = get_logger(__name__)

# Restricted topics
RESTRICTED_TOPICS = [
    "legal advice",
    "medical advice",
    "pricing negotiation",
    "financial advice",
    "political discussions",
]

TOPIC_FILTER_PROMPT = """You are a topic classifier for a guest accommodation service.

Your job is to determine if the guest's message is asking about a RESTRICTED topic.

Restricted topics include:
- Legal advice (e.g., "Can I sue the hotel?", "What are my legal rights?")
- Medical advice (e.g., "I have symptoms, what should I do?", "What medication should I take?")
- Pricing negotiation (e.g., "Can you give me a discount?", "I want a lower price")
- Financial advice (e.g., "Should I invest in this?", "How should I manage my money?")
- Political discussions (e.g., political opinions, debates)

Allowed topics include:
- Property information (check-in times, amenities, parking)
- Reservation details (dates, room types, special requests)
- General accommodation questions
- Directions and local information
- Facilities and services

Guest message: {message}

Is this message asking about a RESTRICTED topic?

Respond in JSON format:
{{
    "restricted": true/false,
    "topic": "the identified topic or 'general'",
    "reason": "brief explanation"
}}
"""


async def check_topic_restriction(message: str) -> Dict[str, Any]:
    """
    Check if message contains restricted topics.

    Returns:
        Dict with keys: allowed (bool), reason (str), topic (str)
    """
    settings = get_settings()

    # Initialize LLM
    llm = ChatDeepSeek(
        model=settings.llm_model,
        temperature=0,
        api_key=settings.deepseek_api_key,
    )

    # Classify topic
    prompt = TOPIC_FILTER_PROMPT.format(message=message)
    logger.debug(f"Topic filter prompt for message: {message[:50]}...")

    response = await llm.ainvoke(prompt)
    logger.debug(f"Topic filter raw response: {response.content[:200]}")

    # Parse response
    try:
        content = response.content

        # Strip markdown code blocks if present
        if "```json" in content:
            match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
        elif "```" in content:
            match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)

        result = json.loads(content)
        restricted = result.get("restricted", False)

        if restricted:
            guardrail_triggered.labels(guardrail_type="topic_filter").inc()
            logger.info(f"Topic restricted: {result.get('topic')} - {result.get('reason')}")

        return {
            "allowed": not restricted,
            "reason": result.get("reason", ""),
            "topic": result.get("topic", "general"),
        }
    except (json.JSONDecodeError, AttributeError) as e:
        # Log the error for debugging
        logger.error(f"Failed to parse topic filter response: {response.content[:200]}")
        logger.error(f"Parse error: {str(e)}")

        # Default to allowed if parsing fails
        return {
            "allowed": True,
            "reason": "Classification failed, defaulting to allowed",
            "topic": "general",
        }
