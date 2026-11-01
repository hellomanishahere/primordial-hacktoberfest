"""Core package containing configuration, exceptions, and logging."""

from app.core.config import settings
from app.core.exceptions import (
    AIModelResponseException,
    AIModelTimeoutException,
    AIServiceUnavailableException,
    EmptyDiscussionException,
    GitHubAPIException,
    GitHubAuthenticationException,
    GitHubForbiddenException,
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    GitHubTimeoutException,
    InvalidGitHubURLException,
    PrimordialException,
    SchemaValidationException,
)
from app.core.logging import get_logger, setup_logging

__all__ = [
    "settings",
    "PrimordialException",
    "InvalidGitHubURLException",
    "GitHubResourceNotFoundException",
    "GitHubRateLimitExceededException",
    "GitHubAuthenticationException",
    "GitHubForbiddenException",
    "GitHubTimeoutException",
    "GitHubAPIException",
    "EmptyDiscussionException",
    "AIServiceUnavailableException",
    "AIModelTimeoutException",
    "AIModelResponseException",
    "SchemaValidationException",
    "get_logger",
    "setup_logging",
]
