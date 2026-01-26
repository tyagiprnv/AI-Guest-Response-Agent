"""
Template substitution module for direct template responses.

This module enables skipping LLM calls for high-confidence template matches
by performing runtime substitution of placeholders with live property/reservation data.
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


def build_context(
    property_details: Optional[Dict[str, Any]],
    reservation_details: Optional[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Build a unified context dictionary from property and reservation data.

    Args:
        property_details: Property data dict (from get_property_info)
        reservation_details: Reservation data dict (from get_reservation_info)

    Returns:
        Dict mapping placeholder names to their values
    """
    context: Dict[str, str] = {}

    # Extract property details
    if property_details:
        context["check_in_time"] = property_details.get("check_in_time", "")
        context["check_out_time"] = property_details.get("check_out_time", "")
        context["parking_details"] = property_details.get("parking_details", "")
        context["property_name"] = property_details.get("name", "")

        # Format amenities list
        amenities = property_details.get("amenities", [])
        if amenities:
            context["amenities_list"] = ", ".join(amenities)

        # Extract policies
        policies = property_details.get("policies", {})
        if policies:
            context["cancellation_policy"] = policies.get("cancellation_policy", "")
            context["pets_allowed"] = "Yes" if policies.get("pets_allowed") else "No"
            context["smoking_allowed"] = "Yes" if policies.get("smoking_allowed") else "No"

        # Extract contact info
        contact = property_details.get("contact_info", {})
        if contact:
            context["contact_phone"] = contact.get("phone", "")
            context["contact_email"] = contact.get("email", "")

    # Extract reservation details
    if reservation_details:
        context["guest_name"] = reservation_details.get("guest_name", "")
        context["guest_count"] = str(reservation_details.get("guest_count", ""))

        # Format room type
        room_type = reservation_details.get("room_type", "")
        if room_type:
            context["room_type"] = room_type.title()

        # Format dates
        check_in_date = reservation_details.get("check_in_date")
        if check_in_date:
            context["reservation_check_in"] = _format_date(check_in_date)

        check_out_date = reservation_details.get("check_out_date")
        if check_out_date:
            context["reservation_check_out"] = _format_date(check_out_date)

        # Format special requests
        special_requests = reservation_details.get("special_requests", [])
        if special_requests:
            context["special_requests"] = ", ".join(special_requests)

    return context


def _format_date(date_value: Any) -> str:
    """Format a date value for display."""
    if isinstance(date_value, str):
        try:
            dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            return dt.strftime("%B %d, %Y")
        except ValueError:
            return date_value
    elif isinstance(date_value, datetime):
        return date_value.strftime("%B %d, %Y")
    return str(date_value)


def substitute_template(template_text: str, context: Dict[str, str]) -> Tuple[str, list[str]]:
    """
    Replace placeholders in template with values from context.

    Args:
        template_text: Template string with {placeholder} syntax
        context: Dict mapping placeholder names to values

    Returns:
        Tuple of (substituted_text, list of unfilled placeholder names)
    """
    # Find all placeholders in the template
    placeholder_pattern = r"\{(\w+)\}"
    placeholders = re.findall(placeholder_pattern, template_text)

    unfilled = []
    result = template_text

    for placeholder in placeholders:
        value = context.get(placeholder, "")
        if value:
            result = result.replace(f"{{{placeholder}}}", str(value))
        else:
            unfilled.append(placeholder)

    return result, unfilled


def can_use_direct_substitution(
    template: Dict[str, Any],
    context: Dict[str, str],
    score_threshold: float = 0.85
) -> Tuple[bool, str, list[str]]:
    """
    Check if a template can be used for direct substitution.

    Args:
        template: Template dict with 'score' and 'payload' keys
        context: Context dict from build_context()
        score_threshold: Minimum similarity score required

    Returns:
        Tuple of (can_substitute, substituted_text, unfilled_placeholders)
    """
    # Check score threshold
    score = template.get("score", 0)
    if score < score_threshold:
        return False, "", []

    # Get template text
    payload = template.get("payload", {})
    template_text = payload.get("text", "")

    if not template_text:
        return False, "", []

    # Attempt substitution
    substituted_text, unfilled = substitute_template(template_text, context)

    # Can only use direct substitution if all placeholders are filled
    can_substitute = len(unfilled) == 0

    return can_substitute, substituted_text, unfilled


def get_placeholder_names(template_text: str) -> list[str]:
    """
    Extract all placeholder names from a template.

    Args:
        template_text: Template string with {placeholder} syntax

    Returns:
        List of placeholder names found in the template
    """
    placeholder_pattern = r"\{(\w+)\}"
    return re.findall(placeholder_pattern, template_text)
