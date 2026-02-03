"""
Property details lookup tool.
"""
from typing import Any, Dict

from langchain.tools import BaseTool
from pydantic import Field

from src.data.cache import tool_result_cache
from src.data.repositories import get_property_repository
from src.monitoring.metrics import cache_hit, cache_miss, track_tool_execution


class PropertyDetailsTool(BaseTool):
    """Tool for retrieving property details."""

    name: str = "property_details"
    description: str = """
    Retrieves detailed information about a property.
    Use this tool when you need to know about check-in/out times, parking, amenities, or policies.

    Input should be the property ID as a string.

    Returns property information including check-in time, amenities, parking, and policies.
    """

    @track_tool_execution("property_details")
    async def _arun(self, property_id: str) -> str:
        """Async implementation of property details lookup."""
        # Check cache
        cache_key = f"property:{property_id}"
        cached = tool_result_cache.get(cache_key)
        if cached:
            cache_hit.labels(cache_type="tool_result").inc()
            return cached

        cache_miss.labels(cache_type="tool_result").inc()

        # Get property from repository
        repo = get_property_repository()
        property = await repo.get_by_id(property_id)

        if not property:
            result = f"Property {property_id} not found."
            return result

        # Format property details
        result = f"""Property: {property.name}

Check-in: {property.check_in_time}
Check-out: {property.check_out_time}

Parking: {property.parking_details}

Amenities: {', '.join(property.amenities)}

Policies:
- Pets allowed: {'Yes' if property.policies.get('pets_allowed') else 'No'}
- Cancellation: {property.policies.get('cancellation_policy', 'N/A')}

Contact:
- Phone: {property.contact_info.get('phone', 'N/A')}
- Email: {property.contact_info.get('email', 'N/A')}
"""

        # Cache result
        tool_result_cache.set(cache_key, result)

        return result

    def _run(self, property_id: str) -> str:
        """Sync implementation (not supported)."""
        raise NotImplementedError("Use async version")


async def get_property_info(property_id: str) -> Dict[str, Any] | None:
    """Get property information (direct function for use in agent)."""
    # Check cache
    cache_key = f"property:{property_id}"
    cached = tool_result_cache.get(cache_key)
    if cached:
        cache_hit.labels(cache_type="tool_result").inc()
        return cached

    cache_miss.labels(cache_type="tool_result").inc()

    # Get property from repository
    repo = get_property_repository()
    property = await repo.get_by_id(property_id)

    if not property:
        return None

    # Use mode="json" to ensure proper serialization of enums
    result = property.model_dump(mode="json")

    # Cache result
    tool_result_cache.set(cache_key, result)

    return result
