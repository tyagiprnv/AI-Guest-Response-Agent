"""
LLM cost calculation and tracking.
"""
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    input_price: float  # Per million tokens
    output_price: float  # Per million tokens


# Groq model pricing (as of 2026)
# https://groq.com/pricing/
MODEL_PRICING = {
    "llama-3.1-8b-instant": ModelPricing(input_price=0.05, output_price=0.08),
    "llama-3.1-70b-versatile": ModelPricing(input_price=0.59, output_price=0.79),
    "llama-3.2-1b-preview": ModelPricing(input_price=0.04, output_price=0.04),
    "llama-3.2-3b-preview": ModelPricing(input_price=0.06, output_price=0.06),
    "llama-3.2-11b-vision-preview": ModelPricing(input_price=0.18, output_price=0.18),
    "llama-3.2-90b-vision-preview": ModelPricing(input_price=0.90, output_price=0.90),
    # Add more models as needed
}


def calculate_llm_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate the cost of an LLM call.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name

    Returns:
        Cost in USD
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        # Unknown model, return 0
        return 0.0

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * pricing.input_price
    output_cost = (output_tokens / 1_000_000) * pricing.output_price

    total_cost = input_cost + output_cost

    return total_cost


def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted cost string
    """
    if cost < 0.01:
        return f"${cost * 1000:.4f}m"  # Display in millicents for very small values
    return f"${cost:.6f}"
