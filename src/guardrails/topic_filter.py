"""
Topic filter to restrict certain types of queries.
"""
from typing import Dict

from langchain_deepseek import ChatDeepSeek

from src.config.settings import get_settings
from src.monitoring.metrics import guardrail_triggered

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


async def check_topic_restriction(message: str) -> Dict[str, any]:
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
    response = await llm.ainvoke(prompt)

    # Parse response
    import json
    try:
        result = json.loads(response.content)
        restricted = result.get("restricted", False)

        if restricted:
            guardrail_triggered.labels(guardrail_type="topic_filter").inc()

        return {
            "allowed": not restricted,
            "reason": result.get("reason", ""),
            "topic": result.get("topic", "general"),
        }
    except json.JSONDecodeError:
        # Default to allowed if parsing fails
        return {
            "allowed": True,
            "reason": "Classification failed, defaulting to allowed",
            "topic": "general",
        }
