"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"

    # Mock API keys if not present
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-openai-key"

    if not os.environ.get("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = "test-deepseek-key"

    yield

    # Cleanup after tests
    if os.environ.get("ENVIRONMENT") == "test":
        os.environ.pop("ENVIRONMENT", None)


@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding generation."""
    return [0.1] * 1536  # Standard embedding size


@pytest.fixture
def mock_property_data():
    """Mock property data for testing."""
    return {
        "id": "prop_001",
        "name": "Test Hotel",
        "check_in_time": "3:00 PM",
        "check_out_time": "11:00 AM",
        "parking": "free",
        "parking_details": "Free parking available",
        "amenities": ["WiFi", "Pool", "Gym"],
        "policies": {
            "pets_allowed": False,
            "smoking_allowed": False,
            "cancellation_policy": "Free cancellation up to 24 hours before check-in"
        },
        "contact_info": {
            "phone": "555-0100",
            "email": "contact@testhotel.com"
        }
    }


@pytest.fixture
def mock_reservation_data():
    """Mock reservation data for testing."""
    from datetime import datetime

    return {
        "id": "res_001",
        "property_id": "prop_001",
        "guest_name": "John Doe",
        "guest_email": "john@example.com",
        "check_in_date": datetime(2024, 3, 15, 15, 0),
        "check_out_date": datetime(2024, 3, 18, 11, 0),
        "room_type": "deluxe",
        "guest_count": 2,
        "special_requests": ["Early check-in", "High floor"]
    }


@pytest.fixture
def mock_template_data():
    """Mock template data for testing."""
    return [
        {
            "template": "Check-in is available from 3:00 PM onwards.",
            "category": "check_in",
            "metadata": {"language": "en"},
            "similarity_score": 0.92
        },
        {
            "template": "Our standard check-in time is 3:00 PM.",
            "category": "check_in",
            "metadata": {"language": "en"},
            "similarity_score": 0.88
        },
        {
            "template": "You can check in starting at 3 PM.",
            "category": "check_in",
            "metadata": {"language": "en"},
            "similarity_score": 0.85
        }
    ]


@pytest.fixture
def sample_guest_messages():
    """Sample guest messages for testing."""
    return {
        "check_in": "What time is check-in?",
        "check_out": "What time is check-out?",
        "parking": "Is parking available?",
        "amenities": "What amenities do you have?",
        "wifi": "What's the WiFi password?",
        "policies": "What is your cancellation policy?",
        "special_request": "Can I request early check-in?",
        "pii_email": "My email is test@example.com",
        "pii_ssn": "My SSN is 123-45-6789",
        "restricted_legal": "Can you help me sue someone?",
        "restricted_medical": "I have a fever, should I take antibiotics?",
        "restricted_financial": "Can you give me a discount?",
    }


@pytest.fixture
def clear_caches():
    """Clear all caches before each test."""
    from src.data.cache import embedding_cache, tool_result_cache, response_cache

    # Clear caches
    embedding_cache.clear()
    tool_result_cache.clear()
    response_cache.clear()

    yield

    # Clear again after test
    embedding_cache.clear()
    tool_result_cache.clear()
    response_cache.clear()
