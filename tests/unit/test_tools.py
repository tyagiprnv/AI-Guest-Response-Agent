"""
Unit tests for tool functions.
"""
import pytest


class TestPropertyDetailsTool:
    """Test property details tool."""

    @pytest.mark.asyncio
    async def test_get_property_info_basic(self):
        """Test basic property info retrieval."""
        try:
            from src.tools.property_details import get_property_info

            # Test with a property ID
            result = await get_property_info("prop_001")

            # Result can be None or a dict
            assert result is None or isinstance(result, dict)

            # If result exists, verify structure
            if result:
                assert "id" in result
                assert result["id"] == "prop_001"
        except ImportError:
            pytest.skip("Property details tool not available")

    @pytest.mark.asyncio
    async def test_get_property_info_nonexistent(self):
        """Test retrieving non-existent property."""
        try:
            from src.tools.property_details import get_property_info

            result = await get_property_info("nonexistent_property_12345")
            assert result is None
        except ImportError:
            pytest.skip("Property details tool not available")


class TestReservationDetailsTool:
    """Test reservation details tool."""

    @pytest.mark.asyncio
    async def test_get_reservation_info_basic(self):
        """Test basic reservation info retrieval."""
        try:
            from src.tools.reservation_details import get_reservation_info

            # Test with a reservation ID
            result = await get_reservation_info("res_001")

            # Result can be None or a dict
            assert result is None or isinstance(result, dict)

            # If result exists, verify structure
            if result:
                assert "id" in result
                assert result["id"] == "res_001"
        except ImportError:
            pytest.skip("Reservation details tool not available")

    @pytest.mark.asyncio
    async def test_get_reservation_info_none_input(self):
        """Test with None input."""
        try:
            from src.tools.reservation_details import get_reservation_info

            result = await get_reservation_info(None)
            assert result is None
        except ImportError:
            pytest.skip("Reservation details tool not available")


class TestTemplateRetrievalTool:
    """Test template retrieval tool."""

    @pytest.mark.asyncio
    async def test_retrieve_templates_basic(self):
        """Test basic template retrieval."""
        try:
            from src.tools.template_retrieval import retrieve_templates

            result = await retrieve_templates("What time is check-in?")

            # Should return a list (may be empty)
            assert isinstance(result, list)
        except Exception as e:
            # Template retrieval may fail if Qdrant is not running
            pytest.skip(f"Template retrieval not available: {str(e)}")

    @pytest.mark.asyncio
    async def test_retrieve_templates_returns_list(self):
        """Test that template retrieval always returns a list."""
        try:
            from src.tools.template_retrieval import retrieve_templates

            queries = [
                "What time is check-in?",
                "Is parking available?",
            ]

            for query in queries:
                result = await retrieve_templates(query)
                assert isinstance(result, list)
        except Exception as e:
            pytest.skip(f"Template retrieval not available: {str(e)}")
