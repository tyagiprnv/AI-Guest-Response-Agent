"""
Unit tests for the template substitution module.
"""
import pytest
from src.tools.template_substitution import (
    build_context,
    substitute_template,
    can_use_direct_substitution,
    get_placeholder_names,
)


class TestBuildContext:
    """Tests for the build_context function."""

    def test_build_context_with_property_data(self):
        """Test context building with property data only."""
        property_data = {
            "name": "Test Hotel",
            "check_in_time": "3:00 PM",
            "check_out_time": "11:00 AM",
            "parking_details": "Free parking available",
            "amenities": ["WiFi", "Pool", "Gym"],
            "policies": {
                "pets_allowed": True,
                "smoking_allowed": False,
                "cancellation_policy": "Free cancellation up to 24 hours",
            },
            "contact_info": {
                "phone": "555-1234",
                "email": "test@hotel.com",
            },
        }

        context = build_context(property_data, None)

        assert context["check_in_time"] == "3:00 PM"
        assert context["check_out_time"] == "11:00 AM"
        assert context["parking_details"] == "Free parking available"
        assert context["property_name"] == "Test Hotel"
        assert context["amenities_list"] == "WiFi, Pool, Gym"
        assert context["cancellation_policy"] == "Free cancellation up to 24 hours"
        assert context["pets_allowed"] == "Yes"
        assert context["smoking_allowed"] == "No"
        assert context["contact_phone"] == "555-1234"
        assert context["contact_email"] == "test@hotel.com"

    def test_build_context_with_reservation_data(self):
        """Test context building with reservation data only."""
        reservation_data = {
            "guest_name": "John Doe",
            "room_type": "deluxe",
            "check_in_date": "2025-06-15T15:00:00",
            "check_out_date": "2025-06-18T11:00:00",
            "guest_count": 2,
            "special_requests": ["Early check-in", "High floor"],
        }

        context = build_context(None, reservation_data)

        assert context["guest_name"] == "John Doe"
        assert context["room_type"] == "Deluxe"
        assert context["guest_count"] == "2"
        assert context["reservation_check_in"] == "June 15, 2025"
        assert context["reservation_check_out"] == "June 18, 2025"
        assert context["special_requests"] == "Early check-in, High floor"

    def test_build_context_with_both_sources(self):
        """Test context building with both property and reservation data."""
        property_data = {
            "name": "Grand Hotel",
            "check_in_time": "2:00 PM",
            "check_out_time": "12:00 PM",
        }
        reservation_data = {
            "guest_name": "Jane Smith",
            "room_type": "suite",
            "check_in_date": "2025-07-01T14:00:00",
            "check_out_date": "2025-07-05T12:00:00",
        }

        context = build_context(property_data, reservation_data)

        # Property data
        assert context["check_in_time"] == "2:00 PM"
        assert context["property_name"] == "Grand Hotel"

        # Reservation data
        assert context["guest_name"] == "Jane Smith"
        assert context["room_type"] == "Suite"

    def test_build_context_with_empty_inputs(self):
        """Test context building with no data."""
        context = build_context(None, None)
        assert context == {}

    def test_build_context_pets_not_allowed(self):
        """Test that pets_allowed is 'No' when false."""
        property_data = {
            "policies": {"pets_allowed": False},
        }

        context = build_context(property_data, None)
        assert context["pets_allowed"] == "No"


class TestSubstituteTemplate:
    """Tests for the substitute_template function."""

    def test_substitute_single_placeholder(self):
        """Test substitution of a single placeholder."""
        template = "Check-in is at {check_in_time}."
        context = {"check_in_time": "3:00 PM"}

        result, unfilled = substitute_template(template, context)

        assert result == "Check-in is at 3:00 PM."
        assert unfilled == []

    def test_substitute_multiple_placeholders(self):
        """Test substitution of multiple placeholders."""
        template = "Check-in is at {check_in_time} and check-out is at {check_out_time}."
        context = {"check_in_time": "3:00 PM", "check_out_time": "11:00 AM"}

        result, unfilled = substitute_template(template, context)

        assert result == "Check-in is at 3:00 PM and check-out is at 11:00 AM."
        assert unfilled == []

    def test_unfilled_placeholder(self):
        """Test that unfilled placeholders are tracked."""
        template = "Your amenities: {amenities_list}. Pool hours: {pool_hours}."
        context = {"amenities_list": "WiFi, Gym"}

        result, unfilled = substitute_template(template, context)

        assert "WiFi, Gym" in result
        assert "{pool_hours}" in result
        assert "pool_hours" in unfilled

    def test_no_placeholders(self):
        """Test template with no placeholders."""
        template = "Smoking is not permitted inside the property."
        context = {"check_in_time": "3:00 PM"}

        result, unfilled = substitute_template(template, context)

        assert result == template
        assert unfilled == []

    def test_empty_context(self):
        """Test substitution with empty context."""
        template = "Check-in is at {check_in_time}."
        context = {}

        result, unfilled = substitute_template(template, context)

        assert result == "Check-in is at {check_in_time}."
        assert unfilled == ["check_in_time"]


class TestCanUseDirectSubstitution:
    """Tests for the can_use_direct_substitution function."""

    def test_high_score_all_placeholders_filled(self):
        """Test that high score + all placeholders = can substitute."""
        template = {
            "score": 0.92,
            "payload": {"text": "Check-in begins at {check_in_time}."},
        }
        context = {"check_in_time": "3:00 PM"}

        can_sub, text, unfilled = can_use_direct_substitution(template, context)

        assert can_sub is True
        assert text == "Check-in begins at 3:00 PM."
        assert unfilled == []

    def test_low_score_rejected(self):
        """Test that low score = cannot substitute."""
        template = {
            "score": 0.75,
            "payload": {"text": "Check-in begins at {check_in_time}."},
        }
        context = {"check_in_time": "3:00 PM"}

        can_sub, text, unfilled = can_use_direct_substitution(
            template, context, score_threshold=0.85
        )

        assert can_sub is False

    def test_unfilled_placeholders_rejected(self):
        """Test that unfilled placeholders = cannot substitute."""
        template = {
            "score": 0.92,
            "payload": {"text": "Your room: {room_type}. Request: {special_request}."},
        }
        context = {"room_type": "Deluxe"}

        can_sub, text, unfilled = can_use_direct_substitution(template, context)

        assert can_sub is False
        assert "special_request" in unfilled

    def test_empty_template_text(self):
        """Test handling of empty template text."""
        template = {
            "score": 0.92,
            "payload": {"text": ""},
        }
        context = {"check_in_time": "3:00 PM"}

        can_sub, text, unfilled = can_use_direct_substitution(template, context)

        assert can_sub is False

    def test_custom_threshold(self):
        """Test with custom score threshold."""
        template = {
            "score": 0.80,
            "payload": {"text": "Check-in at {check_in_time}."},
        }
        context = {"check_in_time": "3:00 PM"}

        # Should fail at 0.85 threshold
        can_sub, _, _ = can_use_direct_substitution(
            template, context, score_threshold=0.85
        )
        assert can_sub is False

        # Should pass at 0.75 threshold
        can_sub, _, _ = can_use_direct_substitution(
            template, context, score_threshold=0.75
        )
        assert can_sub is True


class TestGetPlaceholderNames:
    """Tests for the get_placeholder_names function."""

    def test_single_placeholder(self):
        """Test extracting single placeholder."""
        template = "Check-in is at {check_in_time}."
        placeholders = get_placeholder_names(template)
        assert placeholders == ["check_in_time"]

    def test_multiple_placeholders(self):
        """Test extracting multiple placeholders."""
        template = "{greeting}, your room is {room_type} with {amenities_list}."
        placeholders = get_placeholder_names(template)
        assert placeholders == ["greeting", "room_type", "amenities_list"]

    def test_no_placeholders(self):
        """Test template with no placeholders."""
        template = "Welcome to our hotel!"
        placeholders = get_placeholder_names(template)
        assert placeholders == []

    def test_duplicate_placeholders(self):
        """Test that duplicates are included."""
        template = "{time} is check-in. {time} is also good."
        placeholders = get_placeholder_names(template)
        assert placeholders == ["time", "time"]
