"""
Structured logging configuration.
"""
import logging
import sys
from typing import Any

from src.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Set up logging configuration."""
    settings = get_settings()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter in production
    if settings.is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        handlers=[handler],
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
