"""
FastAPI dependencies for authentication.
"""
from fastapi import Security
from fastapi.security import APIKeyHeader

from src.auth.api_key import validate_api_key

# API key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency to validate API key from header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    return validate_api_key(api_key)
