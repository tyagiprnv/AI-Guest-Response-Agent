"""
PII redaction using Microsoft Presidio.
"""
from typing import Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

from src.monitoring.metrics import guardrail_triggered, pii_detected

# Configure NLP engine to use small spaCy model
nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}

# Initialize Presidio engines with explicit small model configuration
nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()


async def detect_and_redact_pii(text: str) -> Tuple[str, bool]:
    """
    Detect and redact PII from text.

    Returns:
        Tuple of (redacted_text, pii_detected_bool)
    """
    # Analyze text for PII
    results = analyzer.analyze(
        text=text,
        language='en',
        entities=[
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "US_SSN",
            "IBAN_CODE",
            "PERSON",
        ],
    )

    # Check if PII was detected
    has_pii = len(results) > 0

    if has_pii:
        # Anonymize the text
        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=results,
        )
        redacted_text = anonymized.text

        # Update metrics
        pii_detected.inc()
        guardrail_triggered.labels(guardrail_type="pii_redaction").inc()

        return redacted_text, True

    return text, False


def should_block_pii(text: str) -> bool:
    """
    Check if text contains sensitive PII that should block the request.

    Some PII like SSN, credit cards should block the request entirely.
    """
    results = analyzer.analyze(
        text=text,
        language='en',
        entities=["CREDIT_CARD", "US_SSN", "IBAN_CODE"],
    )

    return len(results) > 0
