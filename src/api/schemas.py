"""
API request and response schemas.
"""
import re
import unicodedata
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator


class GenerateResponseRequest(BaseModel):
    """Request schema for generating a response."""

    message: str = Field(
        ...,
        description="Guest message/query",
        min_length=3,
        max_length=1000,
    )
    property_id: str = Field(
        ...,
        description="Property ID",
        pattern=r"^prop_\d{3}$",
    )
    reservation_id: str | None = Field(
        None,
        description="Optional reservation ID",
        pattern=r"^res_\d{3}$",
    )

    @field_validator("message")
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        """Validate message content."""
        # Reject spam patterns (repeated characters)
        if re.match(r"^(.)\1{10,}$", v):
            raise ValueError("Message contains spam pattern (repeated characters)")

        # Count URLs in message
        url_count = len(re.findall(r"https?://", v))
        if url_count > 2:
            raise ValueError("Too many URLs in message (maximum 2 allowed)")

        # Unicode normalization (NFKC form)
        normalized = unicodedata.normalize("NFKC", v)

        return normalized

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What time is check-in?",
                "property_id": "prop_001",
                "reservation_id": "res_001",
            }
        }


class ResponseMetadata(BaseModel):
    """Metadata about the response generation."""

    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    pii_detected: bool = Field(default=False, description="Whether PII was detected")
    templates_found: int = Field(default=0, description="Number of templates found")
    error: str | None = Field(None, description="Error message if any")


class GenerateResponseResponse(BaseModel):
    """Response schema for generated responses."""

    response_text: str = Field(..., description="Generated response text")
    response_type: str = Field(
        ..., description="Type of response (template/custom/no_response/error)"
    )
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    metadata: ResponseMetadata = Field(..., description="Response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "response_text": "Check-in is available from 3:00 PM onwards.",
                "response_type": "template",
                "confidence_score": 0.92,
                "metadata": {
                    "execution_time_ms": 450.5,
                    "pii_detected": False,
                    "templates_found": 3,
                },
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")
    request_id: str | None = Field(None, description="Request ID for tracking")
