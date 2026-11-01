"""Structured logging configuration for Primordial."""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configures application-wide structured logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger configured with application settings."""
    return logging.getLogger(name)

