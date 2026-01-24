"""
API middleware for rate limiting, CORS, and logging.
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import get_settings
from src.monitoring.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host

        # Clean old requests
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] if req_time > cutoff
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        # Add current request
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started - {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed - {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                },
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(duration)

            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed - {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration": duration,
                },
            )
            raise


def setup_middleware(app):
    """Set up all middleware."""
    settings = get_settings()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_per_minute,
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
