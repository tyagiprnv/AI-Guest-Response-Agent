"""
Evaluate response quality using GPT-4 as a judge.

Scores responses on:
- Actionability (0-10): Provides concrete next steps
- Context usage (0-10): Uses available property/reservation data
- Persona (0-10): Speaks AS the property (not middleman)
- Helpfulness (0-10): Actually useful to guest
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI

from src.agent.graph import run_agent
from src.config.settings import get_settings
from src.tools.property_details import get_property_info
from src.tools.reservation_details import get_reservation_info


async def evaluate_response(
    query: str,
    response: str,
    property_data: dict,
    reservation_data: dict,
) -> dict:
    """Score response quality using LLM judge."""

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Extract relevant context for evaluation
    property_name = property_data.get("name", "Unknown Property")
    check_in_time = property_data.get("check_in_time", "N/A")
    phone = property_data.get("contact_info", {}).get("phone", "N/A")
    check_in_date = reservation_data.get("check_in_date", "N/A") if reservation_data else "N/A"
    room_type = reservation_data.get("room_type", "N/A") if reservation_data else "N/A"

    prompt = f"""Evaluate this AI guest response on a scale of 0-10 for each criterion:

Guest Query: {query}
AI Response: {response}

Available Context:
- Property: {property_name}, Check-in: {check_in_time}, Phone: {phone}
- Reservation: Check-in {check_in_date}, Room: {room_type}

Criteria:
1. Actionability: Does it provide concrete next steps? (0=vague, 10=specific actions)
2. Context Usage: Uses available property/reservation data? (0=ignores, 10=leverages all)
3. Persona: Speaks AS the property (not middleman)? (0=3rd person, 10=uses "we"/"our")
4. Helpfulness: Actually useful to guest? (0=generic/unhelpful, 10=solves problem)

Return JSON only:
{{
    "actionability": <score>,
    "context_usage": <score>,
    "persona": <score>,
    "helpfulness": <score>,
    "overall": <average>,
    "reasoning": "brief explanation"
}}
"""

    response_obj = await client.chat.completions.create(
        model="gpt-4o-mini",  # Fast and cheap
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    return json.loads(response_obj.choices[0].message.content)


async def run_evaluation():
    """Run evaluation on key test cases."""
    test_cases = [
        {
            "name": "Flight Delay (Travel Issue)",
            "message": "my flight is delayed, what should I do",
            "property_id": "prop_081",
            "reservation_id": "res_054",
        },
        {
            "name": "Late Arrival",
            "message": "we're running late, will be there around 10pm",
            "property_id": "prop_081",
            "reservation_id": "res_054",
        },
        {
            "name": "Extend Stay",
            "message": "I need to extend my stay by 2 nights",
            "property_id": "prop_081",
            "reservation_id": "res_054",
        },
        {
            "name": "Parking Question",
            "message": "is parking available at the property",
            "property_id": "prop_081",
            "reservation_id": "res_054",
        },
        {
            "name": "Check-in Time",
            "message": "what time can I check in",
            "property_id": "prop_081",
            "reservation_id": "res_054",
        },
    ]

    total_scores = {
        "actionability": 0,
        "context_usage": 0,
        "persona": 0,
        "helpfulness": 0,
        "overall": 0,
    }

    print("=" * 80)
    print("RESPONSE QUALITY EVALUATION")
    print("=" * 80)
    print()

    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print("-" * 80)
        print(f"Query: {test['message']}")
        print()

        # Get agent response
        try:
            result = await run_agent(
                guest_message=test["message"],
                property_id=test["property_id"],
                reservation_id=test.get("reservation_id"),
            )

            response = result["response_text"]
            print(f"Response: {response}")
            print()

            # Fetch property and reservation data for evaluation context
            property_data = await get_property_info(test["property_id"])
            reservation_data = None
            if test.get("reservation_id"):
                reservation_data = await get_reservation_info(test["reservation_id"])

            # Evaluate quality
            scores = await evaluate_response(
                query=test["message"],
                response=response,
                property_data=property_data or {},
                reservation_data=reservation_data or {},
            )

            # Display scores
            print(f"Scores:")
            print(f"  Actionability:  {scores['actionability']}/10")
            print(f"  Context Usage:  {scores['context_usage']}/10")
            print(f"  Persona:        {scores['persona']}/10")
            print(f"  Helpfulness:    {scores['helpfulness']}/10")
            print(f"  Overall:        {scores['overall']:.1f}/10")
            print(f"  Reasoning: {scores['reasoning']}")

            # Accumulate totals
            for key in total_scores:
                total_scores[key] += scores[key]

        except Exception as e:
            print(f"ERROR: {e}")
            print()

        print()
        print()

    # Calculate and display averages
    num_tests = len(test_cases)
    print("=" * 80)
    print("AVERAGE SCORES")
    print("=" * 80)
    print(f"Actionability:  {total_scores['actionability'] / num_tests:.1f}/10")
    print(f"Context Usage:  {total_scores['context_usage'] / num_tests:.1f}/10")
    print(f"Persona:        {total_scores['persona'] / num_tests:.1f}/10")
    print(f"Helpfulness:    {total_scores['helpfulness'] / num_tests:.1f}/10")
    print(f"Overall:        {total_scores['overall'] / num_tests:.1f}/10")
    print()

    # Success criteria check
    avg_overall = total_scores['overall'] / num_tests
    if avg_overall >= 8.0:
        print("✅ SUCCESS: Average overall score >= 8.0")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: Average overall score {avg_overall:.1f} < 8.0")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
