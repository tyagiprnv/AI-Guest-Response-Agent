"""
Data models for the application.
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TemplateCategory(str, Enum):
    """Template categories."""

    CHECK_IN = "check-in"
    CHECK_OUT = "check-out"
    PARKING = "parking"
    AMENITIES = "amenities"
    POLICIES = "policies"
    SPECIAL_REQUESTS = "special-requests"
    GENERAL = "general"


class Template(BaseModel):
    """Response template model."""

    id: str = Field(..., description="Unique template ID")
    category: TemplateCategory = Field(..., description="Template category")
    text: str = Field(..., description="Template response text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "T001",
                "category": "check-in",
                "text": "Check-in is available from 3:00 PM onwards.",
                "metadata": {"language": "en", "tone": "professional"},
            }
        }


class ParkingType(str, Enum):
    """Parking types."""

    FREE = "free"
    PAID = "paid"
    NONE = "none"


class Property(BaseModel):
    """Property model."""

    id: str = Field(..., description="Unique property ID")
    name: str = Field(..., description="Property name")
    check_in_time: str = Field(..., description="Check-in time (e.g., '3:00 PM')")
    check_out_time: str = Field(..., description="Check-out time (e.g., '11:00 AM')")
    parking: ParkingType = Field(..., description="Parking type")
    parking_details: str | None = Field(None, description="Parking details")
    amenities: list[str] = Field(default_factory=list, description="List of amenities")
    policies: dict[str, Any] = Field(default_factory=dict, description="Property policies")
    contact_info: dict[str, str] = Field(
        default_factory=dict, description="Contact information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "prop_001",
                "name": "Sunset Beach Resort",
                "check_in_time": "3:00 PM",
                "check_out_time": "11:00 AM",
                "parking": "free",
                "parking_details": "Free parking available on-site",
                "amenities": ["WiFi", "Pool", "Gym", "Breakfast"],
                "policies": {
                    "pets_allowed": False,
                    "smoking_allowed": False,
                    "cancellation_policy": "Free cancellation up to 48 hours before check-in",
                },
                "contact_info": {"phone": "+1-555-0100", "email": "info@sunsetbeach.com"},
            }
        }


class RoomType(str, Enum):
    """Room types."""

    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    STUDIO = "studio"


class Reservation(BaseModel):
    """Reservation model."""

    id: str = Field(..., description="Unique reservation ID")
    property_id: str = Field(..., description="Property ID")
    guest_name: str = Field(..., description="Guest name")
    guest_email: str = Field(..., description="Guest email")
    check_in_date: datetime = Field(..., description="Check-in date")
    check_out_date: datetime = Field(..., description="Check-out date")
    room_type: RoomType = Field(..., description="Room type")
    guest_count: int = Field(..., description="Number of guests")
    special_requests: list[str] = Field(
        default_factory=list, description="Special requests"
    )
    booking_date: datetime = Field(default_factory=datetime.now, description="Booking date")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "res_001",
                "property_id": "prop_001",
                "guest_name": "John Doe",
                "guest_email": "john@example.com",
                "check_in_date": "2024-03-15T15:00:00",
                "check_out_date": "2024-03-18T11:00:00",
                "room_type": "deluxe",
                "guest_count": 2,
                "special_requests": ["Early check-in", "High floor"],
                "booking_date": "2024-02-01T10:30:00",
            }
        }


class TestCase(BaseModel):
    """Test case for evaluation."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique test case ID")
    guest_message: str = Field(..., description="Guest message/query")
    property_id: str = Field(..., description="Property ID")
    reservation_id: str | None = Field(None, description="Reservation ID (optional)")
    expected_response_type: str = Field(
        ..., description="Expected response type (template/custom/no_response)"
    )
    expected_category: TemplateCategory | None = Field(
        None, description="Expected template category"
    )
    ground_truth: str | None = Field(None, description="Ground truth response")
    annotations: dict[str, Any] = Field(
        default_factory=dict, description="Test case annotations"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "test_001",
                "guest_message": "What time is check-in?",
                "property_id": "prop_001",
                "reservation_id": None,
                "expected_response_type": "template",
                "expected_category": "check-in",
                "ground_truth": "Check-in is at 3:00 PM",
                "annotations": {"difficulty": "easy", "ambiguous": False},
            }
        }
