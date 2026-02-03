"""
API key validation logic.
"""
from fastapi import HTTPException, status

from src.config.settings import get_settings


def validate_api_key(api_key: str) -> str:
    """
    Validate API key against configured keys.

    Args:
        api_key: API key to validate

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()

    # If authentication is disabled, allow all requests
    if not settings.auth_enabled:
        return api_key

    # Get configured API keys
    configured_keys = [key.strip() for key in settings.api_keys.split(",") if key.strip()]

    if not configured_keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No API keys configured",
        )

    # Validate API key
    if api_key not in configured_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_api_key_tier(api_key: str) -> str:
    """
    Get rate limit tier for API key.

    In Phase 1, all keys are 'standard' tier.
    In Phase 2 (with database), this will query the database.

    Args:
        api_key: API key

    Returns:
        Rate limit tier (standard, premium, enterprise)
    """
    # TODO: In Phase 2, query database for key metadata
    # For now, return standard tier for all keys
    return "standard"
