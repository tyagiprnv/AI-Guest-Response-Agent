"""
Unit tests for data models.
"""
import pytest
from datetime import datetime

from src.data.models import (
    Property,
    Reservation,
    Template,
    TemplateCategory,
    ParkingType,
    RoomType,
)


class TestTemplateModel:
    """Test Template model."""

    def test_template_creation(self):
        """Test creating a template."""
        template = Template(
            id="T001",
            category=TemplateCategory.CHECK_IN,
            text="Check-in is at 3:00 PM",
            metadata={"language": "en"},
        )

        assert template.id == "T001"
        assert template.category == TemplateCategory.CHECK_IN
        assert template.text == "Check-in is at 3:00 PM"
        assert template.metadata["language"] == "en"

    def test_template_categories(self):
        """Test all template categories."""
        categories = [
            TemplateCategory.CHECK_IN,
            TemplateCategory.CHECK_OUT,
            TemplateCategory.PARKING,
            TemplateCategory.AMENITIES,
            TemplateCategory.POLICIES,
            TemplateCategory.SPECIAL_REQUESTS,
            TemplateCategory.GENERAL,
        ]

        for category in categories:
            template = Template(
                id=f"T_{category.value}",
                category=category,
                text=f"Template for {category.value}",
            )
            assert template.category == category


class TestPropertyModel:
    """Test Property model."""

    def test_property_creation(self):
        """Test creating a property."""
        property = Property(
            id="prop_001",
            name="Test Hotel",
            check_in_time="3:00 PM",
            check_out_time="11:00 AM",
            parking=ParkingType.FREE,
            parking_details="Free parking on-site",
            amenities=["WiFi", "Pool", "Gym"],
            policies={"pets_allowed": False, "smoking_allowed": False},
            contact_info={"phone": "555-0100", "email": "contact@hotel.com"},
        )

        assert property.id == "prop_001"
        assert property.name == "Test Hotel"
        assert property.parking == ParkingType.FREE
        assert len(property.amenities) == 3
        assert "WiFi" in property.amenities
        assert property.policies["pets_allowed"] is False

    def test_parking_types(self):
        """Test all parking types."""
        parking_types = [ParkingType.FREE, ParkingType.PAID, ParkingType.NONE]

        for parking_type in parking_types:
            property = Property(
                id=f"prop_{parking_type.value}",
                name=f"Hotel with {parking_type.value} parking",
                check_in_time="3:00 PM",
                check_out_time="11:00 AM",
                parking=parking_type,
                amenities=["WiFi"],
                policies={},
                contact_info={},
            )
            assert property.parking == parking_type

    def test_property_with_no_parking_details(self):
        """Test property without parking details."""
        property = Property(
            id="prop_002",
            name="No Parking Hotel",
            check_in_time="3:00 PM",
            check_out_time="11:00 AM",
            parking=ParkingType.NONE,
            parking_details=None,
            amenities=["WiFi"],
            policies={},
            contact_info={},
        )

        assert property.parking_details is None


class TestReservationModel:
    """Test Reservation model."""

    def test_reservation_creation(self):
        """Test creating a reservation."""
        reservation = Reservation(
            id="res_001",
            property_id="prop_001",
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in_date=datetime(2024, 3, 15, 15, 0),
            check_out_date=datetime(2024, 3, 18, 11, 0),
            room_type=RoomType.DELUXE,
            guest_count=2,
            special_requests=["Early check-in", "High floor"],
            booking_date=datetime(2024, 2, 1, 10, 0),
        )

        assert reservation.id == "res_001"
        assert reservation.guest_name == "John Doe"
        assert reservation.room_type == RoomType.DELUXE
        assert len(reservation.special_requests) == 2
        assert reservation.guest_count == 2

    def test_room_types(self):
        """Test all room types."""
        room_types = [
            RoomType.STANDARD,
            RoomType.DELUXE,
            RoomType.SUITE,
            RoomType.STUDIO,
        ]

        for room_type in room_types:
            reservation = Reservation(
                id=f"res_{room_type.value}",
                property_id="prop_001",
                guest_name="Guest",
                guest_email="guest@example.com",
                check_in_date=datetime(2024, 3, 15),
                check_out_date=datetime(2024, 3, 18),
                room_type=room_type,
                guest_count=2,
                special_requests=[],
            )
            assert reservation.room_type == room_type

    def test_reservation_with_no_special_requests(self):
        """Test reservation without special requests."""
        reservation = Reservation(
            id="res_002",
            property_id="prop_001",
            guest_name="Jane Smith",
            guest_email="jane@example.com",
            check_in_date=datetime(2024, 4, 1),
            check_out_date=datetime(2024, 4, 3),
            room_type=RoomType.STANDARD,
            guest_count=1,
            special_requests=[],
        )

        assert len(reservation.special_requests) == 0

    def test_reservation_date_calculations(self):
        """Test date-related calculations."""
        check_in = datetime(2024, 3, 15, 15, 0)
        check_out = datetime(2024, 3, 18, 11, 0)

        reservation = Reservation(
            id="res_003",
            property_id="prop_001",
            guest_name="Test Guest",
            guest_email="test@example.com",
            check_in_date=check_in,
            check_out_date=check_out,
            room_type=RoomType.SUITE,
            guest_count=4,
            special_requests=[],
        )

        # Calculate nights (actual days difference is 2.something due to times)
        nights = (reservation.check_out_date - reservation.check_in_date).days
        assert nights == 2  # 2 full days (March 15 3PM to March 18 11AM)
