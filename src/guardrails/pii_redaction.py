"""
PII redaction using Microsoft Presidio.
"""
from typing import Tuple

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
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

# Create custom SSN recognizer with better patterns
ssn_patterns = [
    Pattern(
        name="ssn_pattern_with_dashes",
        regex=r"\b\d{3}-\d{2}-\d{4}\b",
        score=0.85,
    ),
    Pattern(
        name="ssn_pattern_no_dashes",
        regex=r"\b\d{9}\b",
        score=0.6,
    ),
]

ssn_recognizer = PatternRecognizer(
    supported_entity="US_SSN",
    patterns=ssn_patterns,
    context=["ssn", "social security", "social security number"],
)

# Create custom credit card recognizer
credit_card_patterns = [
    Pattern(
        name="credit_card_with_dashes",
        regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        score=0.85,
    ),
]

credit_card_recognizer = PatternRecognizer(
    supported_entity="CREDIT_CARD",
    patterns=credit_card_patterns,
    context=["credit card", "card", "cc", "card number"],
)

# Initialize analyzer with custom recognizers
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=None,  # Use default registry
)

# Add custom recognizers
analyzer.registry.add_recognizer(ssn_recognizer)
analyzer.registry.add_recognizer(credit_card_recognizer)

anonymizer = AnonymizerEngine()


def detect_and_redact_pii(text: str) -> Tuple[str, bool]:
    """
    Detect and redact PII from text.

    Returns:
        Tuple of (redacted_text, pii_detected_bool)
    """
    # Analyze text for PII with lower threshold for better detection
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
        score_threshold=0.3,  # Lower threshold for better detection
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
        score_threshold=0.3,  # Lower threshold for better detection
    )

    return len(results) > 0
