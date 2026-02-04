"""
FastAPI dependencies for authentication.
"""
from typing import Optional

from fastapi import Security
from fastapi.security import APIKeyHeader

from src.auth.api_key import validate_api_key
from src.config.settings import get_settings

# API key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    FastAPI dependency to validate API key from header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key (or None if auth is disabled)

    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()

    # If authentication is disabled, skip validation
    if not settings.auth_enabled:
        return None

    # If auth is enabled but no key provided, validation will fail
    return validate_api_key(api_key or "")
