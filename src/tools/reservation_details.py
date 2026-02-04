"""
Reservation details lookup tool.
"""
from typing import Any, Dict

from langchain.tools import BaseTool
from pydantic import Field

from src.data.cache import tool_result_cache
from src.data.repositories import get_reservation_repository
from src.monitoring.metrics import cache_hit, cache_miss, track_tool_execution


class ReservationDetailsTool(BaseTool):
    """Tool for retrieving reservation details."""

    name: str = "reservation_details"
    description: str = """
    Retrieves detailed information about a specific reservation.
    Use this tool when you need to know about check-in/out dates, room type, or special requests.

    Input should be the reservation ID as a string.

    Returns reservation information including dates, room type, guest count, and special requests.
    """

    @track_tool_execution("reservation_details")
    async def _arun(self, reservation_id: str) -> str:
        """Async implementation of reservation details lookup."""
        # Check cache
        cache_key = f"reservation:{reservation_id}"
        cached = tool_result_cache.get(cache_key)
        if cached:
            cache_hit.labels(cache_type="tool_result").inc()
            return cached

        cache_miss.labels(cache_type="tool_result").inc()

        # Get reservation from repository
        repo = get_reservation_repository()
        reservation = await repo.get_by_id(reservation_id)

        if not reservation:
            result = f"Reservation {reservation_id} not found."
            return result

        # Format reservation details
        special_requests = ', '.join(reservation.special_requests) if reservation.special_requests else 'None'

        result = f"""Reservation Details:

Guest: {reservation.guest_name}
Check-in: {reservation.check_in_date.strftime('%Y-%m-%d %I:%M %p')}
Check-out: {reservation.check_out_date.strftime('%Y-%m-%d %I:%M %p')}
Room Type: {reservation.room_type.value.title()}
Guests: {reservation.guest_count}
Special Requests: {special_requests}
"""

        # Cache result
        tool_result_cache.set(cache_key, result)

        return result

    def _run(self, reservation_id: str) -> str:
        """Sync implementation (not supported)."""
        raise NotImplementedError("Use async version")


async def get_reservation_info(reservation_id: str | None) -> Dict[str, Any] | None:
    """Get reservation information (direct function for use in agent)."""
    if not reservation_id:
        return None

    # Check cache
    cache_key = f"reservation:{reservation_id}"
    cached = await tool_result_cache.get(cache_key)
    if cached:
        cache_hit.labels(cache_type="tool_result").inc()
        return cached

    cache_miss.labels(cache_type="tool_result").inc()

    # Get reservation from repository
    repo = get_reservation_repository()
    reservation = await repo.get_by_id(reservation_id)

    if not reservation:
        return None

    # Use mode="json" to serialize datetime objects to ISO format strings
    result = reservation.model_dump(mode="json")

    # Cache result
    await tool_result_cache.set(cache_key, result)

    return result
