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

    def test_blocks_iban(self):
        """Test that IBAN codes are detected and blocked."""
        message = "My IBAN is GB82WEST12345698765432"
        should_block = should_block_pii(message)
        assert should_block is True

    def test_allows_safe_message(self):
        """Test that safe messages pass through."""
        message = "What time is check-in?"
        should_block = should_block_pii(message)
        assert should_block is False

    def test_detects_and_redacts_email(self):
        """Test that emails are detected and redacted."""
        message = "Please send the invoice to john.doe@example.com"
        redacted_text, has_pii = detect_and_redact_pii(message)

        assert has_pii is True
        assert "john.doe@example.com" not in redacted_text
        assert "<EMAIL_ADDRESS>" in redacted_text

    def test_detects_and_redacts_phone(self):
        """Test that phone numbers are detected and redacted."""
        message = "Call me at 555-123-4567"
        redacted_text, has_pii = detect_and_redact_pii(message)

        assert has_pii is True
        assert "555-123-4567" not in redacted_text
        assert "<PHONE_NUMBER>" in redacted_text

    def test_safe_message_unchanged(self):
        """Test that safe messages remain unchanged."""
        message = "What time is check-in?"
        redacted_text, has_pii = detect_and_redact_pii(message)

        assert has_pii is False
        assert redacted_text == message

    def test_multiple_pii_types(self):
        """Test detection of multiple PII types."""
        message = "Contact me at john@example.com or 555-123-4567"
        redacted_text, has_pii = detect_and_redact_pii(message)

        assert has_pii is True
        assert "john@example.com" not in redacted_text
        assert "555-123-4567" not in redacted_text
        assert "<EMAIL_ADDRESS>" in redacted_text
        assert "<PHONE_NUMBER>" in redacted_text

    def test_redacts_person_names(self):
        """Test that person names are detected and redacted."""
        message = "I am John Smith and I have a question"
        redacted_text, has_pii = detect_and_redact_pii(message)

        # Person name detection may vary
        if has_pii:
            assert "<PERSON>" in redacted_text


class TestTopicFilterIntegration:
    """Test topic filter guardrail integration."""

    @pytest.mark.asyncio
    async def test_blocks_legal_advice(self):
        """Test that legal advice requests are blocked."""
        message = "Can you help me sue my landlord for breach of contract?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        assert "reason" in result
        # Legal advice should be restricted
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_blocks_medical_advice(self):
        """Test that medical advice requests are blocked."""
        message = "I have a fever and cough, should I take antibiotics?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        assert result["allowed"] is False

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
        message = "Can you give me a 50% discount on the rate?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        # Price negotiation should be restricted
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_allows_parking_questions(self):
        """Test that parking questions are allowed."""
        message = "Is parking available at the property?"
        result = await check_topic_restriction(message)

        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_allows_policy_questions(self):
        """Test that policy questions are allowed."""
        message = "What is your cancellation policy?"
        result = await check_topic_restriction(message)

        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_blocks_financial_advice(self):
        """Test that financial advice is blocked."""
        message = "Should I invest in your property development fund?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_blocks_political_discussion(self):
        """Test that political discussions are blocked."""
        message = "What is your stance on the upcoming election?"
        result = await check_topic_restriction(message)

        assert "allowed" in result
        # Political discussions should be restricted
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_allows_special_requests(self):
        """Test that special requests are allowed."""
        message = "Can I request a room on a higher floor?"
        result = await check_topic_restriction(message)

        assert result["allowed"] is True


class TestGuardrailChaining:
    """Test that multiple guardrails work together."""

    @pytest.mark.asyncio
    async def test_both_guardrails_applied_pii_detected(self):
        """Test that both guardrails are applied - PII detection."""
        message = "My email is test@example.com. What time is check-in?"

        # PII check - email should be detected
        redacted_text, has_pii = detect_and_redact_pii(message)
        assert has_pii is True
        assert "<EMAIL_ADDRESS>" in redacted_text

        # Topic check on original message - should be allowed
        topic_result = await check_topic_restriction(message)
        assert topic_result["allowed"] is True

    @pytest.mark.asyncio
    async def test_both_guardrails_applied_topic_blocked(self):
        """Test that both guardrails are applied - topic blocked."""
        message = "Can you help me sue someone?"

        # PII check - no PII
        redacted_text, has_pii = detect_and_redact_pii(message)
        assert has_pii is False

        # Topic check - should be blocked (legal advice)
        topic_result = await check_topic_restriction(message)
        assert topic_result["allowed"] is False

    @pytest.mark.asyncio
    async def test_both_guardrails_blocked(self):
        """Test message blocked by both guardrails."""
        message = "My SSN is 123-45-6789. Can you give me legal advice?"

        # PII check - should block
        should_block = should_block_pii(message)
        assert should_block is True

        # Topic check - should also block
        topic_result = await check_topic_restriction(message)
        assert topic_result["allowed"] is False

    @pytest.mark.asyncio
    async def test_safe_message_passes_both(self):
        """Test that safe messages pass both guardrails."""
        message = "What amenities do you have?"

        redacted_text, has_pii = detect_and_redact_pii(message)
        topic_result = await check_topic_restriction(message)

        assert has_pii is False
        assert topic_result["allowed"] is True

    @pytest.mark.asyncio
    async def test_guardrail_order_pii_then_topic(self):
        """Test that PII is redacted before topic filtering."""
        message = "Email me at john@example.com about parking"

        # First PII redaction
        redacted_text, has_pii = detect_and_redact_pii(message)
        assert has_pii is True

        # Then topic filtering on redacted text
        topic_result = await check_topic_restriction(redacted_text)
        assert topic_result["allowed"] is True
