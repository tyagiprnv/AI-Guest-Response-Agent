"""
Unit tests for data models.
"""
import pytest
from datetime import datetime

from src.data.models import Property, Reservation, Template, TemplateCategory, ParkingType, RoomType


def test_template_model():
    """Test Template model."""
    template = Template(
        id="T001",
        category=TemplateCategory.CHECK_IN,
        text="Check-in is at 3:00 PM",
        metadata={"language": "en"},
    )

    assert template.id == "T001"
    assert template.category == TemplateCategory.CHECK_IN
    assert template.text == "Check-in is at 3:00 PM"


def test_property_model():
    """Test Property model."""
    property = Property(
        id="prop_001",
        name="Test Hotel",
        check_in_time="3:00 PM",
        check_out_time="11:00 AM",
        parking=ParkingType.FREE,
        parking_details="Free parking on-site",
        amenities=["WiFi", "Pool"],
        policies={"pets_allowed": False},
        contact_info={"phone": "555-0100"},
    )

    assert property.id == "prop_001"
    assert property.name == "Test Hotel"
    assert property.parking == ParkingType.FREE
    assert len(property.amenities) == 2


def test_reservation_model():
    """Test Reservation model."""
    reservation = Reservation(
        id="res_001",
        property_id="prop_001",
        guest_name="John Doe",
        guest_email="john@example.com",
        check_in_date=datetime(2024, 3, 15, 15, 0),
        check_out_date=datetime(2024, 3, 18, 11, 0),
        room_type=RoomType.DELUXE,
        guest_count=2,
        special_requests=["Early check-in"],
    )

    assert reservation.id == "res_001"
    assert reservation.guest_name == "John Doe"
    assert reservation.room_type == RoomType.DELUXE
    assert len(reservation.special_requests) == 1
