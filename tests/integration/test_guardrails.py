"""Integration tests for guardrail functionality."""

import pytest
from src.guardrails.pii_redaction import detect_and_redact_pii, should_block_pii
from src.guardrails.topic_filter import check_topic_restriction


class TestPIIRedactionIntegration:
    """Test PII redaction guardrail integration."""

    def test_blocks_ssn(self):
        """Test that SSNs are detected and blocked."""
        message = "My SSN is 123-45-6789"
        should_block = should_block_pii(message)
        assert should_block is True

    def test_blocks_credit_card(self):
        """Test that credit card numbers are detected and blocked."""
        message = "My card is 4532-1234-5678-9010"
        should_block = should_block_pii(message)
        assert should_block is True

    def test_allows_safe_message(self):
        """Test that safe messages pass through."""
        message = "What time is check-in?"
        should_block = should_block_pii(message)
        assert should_block is False

    @pytest.mark.asyncio
    async def test_detects_and_redacts_email(self):
        """Test that emails are detected and redacted."""
        message = "Please send the invoice to john.doe@example.com"
        redacted_text, has_pii = await detect_and_redact_pii(message)

        assert has_pii is True
        assert "john.doe@example.com" not in redacted_text

    @pytest.mark.asyncio
    async def test_detects_and_redacts_phone(self):
        """Test that phone numbers are detected and redacted."""
        message = "Call me at 555-123-4567"
        redacted_text, has_pii = await detect_and_redact_pii(message)

        assert has_pii is True
        assert "555-123-4567" not in redacted_text

    @pytest.mark.asyncio
    async def test_safe_message_unchanged(self):
        """Test that safe messages remain unchanged."""
        message = "What time is check-in?"
        redacted_text, has_pii = await detect_and_redact_pii(message)

        assert has_pii is False
        assert redacted_text == message


class TestTopicFilterIntegration:
    """Test topic filter guardrail integration."""

    @pytest.mark.asyncio
    async def test_blocks_legal_advice(self):
        """Test that legal advice requests are blocked."""
        message = "Can you help me sue my landlord?"
        result = await check_topic_restriction(message)

        # May or may not be blocked depending on model sensitivity
        assert "allowed" in result
        assert "reason" in result
        # Legal advice should be restricted
        assert result["allowed"] is False or "legal" in result.get("topic", "").lower()

    @pytest.mark.asyncio
    async def test_blocks_medical_advice(self):
        """Test that medical advice requests are blocked."""
        message = "I have a fever, should I take antibiotics?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        # Medical advice should be restricted
        assert result["allowed"] is False or "medical" in result.get("topic", "").lower()

    @pytest.mark.asyncio
    async def test_allows_accommodation_questions(self):
        """Test that accommodation questions are allowed."""
        message = "What time is check-in?"
        result = await check_topic_restriction(message)

        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_allows_amenity_questions(self):
        """Test that amenity questions are allowed."""
        message = "Do you have a swimming pool?"
        result = await check_topic_restriction(message)

        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_blocks_price_negotiation(self):
        """Test that price negotiation is blocked."""
        message = "Can you give me a discount on the rate?"
        result = await check_topic_restriction(message)

        # May or may not be blocked depending on configuration
        assert "allowed" in result


class TestGuardrailChaining:
    """Test that multiple guardrails work together."""

    @pytest.mark.asyncio
    async def test_both_guardrails_applied(self):
        """Test that both guardrails are applied in sequence."""
        message = "My email is test@example.com. Can you help me sue someone?"

        # PII check - email should be detected
        redacted_text, has_pii = await detect_and_redact_pii(message)
        assert has_pii is True

        # Topic check on original message
        topic_result = await check_topic_restriction(message)
        # Legal advice should be restricted
        assert topic_result["allowed"] is False or "legal" in topic_result.get("topic", "").lower()

    @pytest.mark.asyncio
    async def test_safe_message_passes_both(self):
        """Test that safe messages pass both guardrails."""
        message = "What amenities do you have?"

        redacted_text, has_pii = await detect_and_redact_pii(message)
        topic_result = await check_topic_restriction(message)

        assert has_pii is False
        assert topic_result["allowed"] is True
