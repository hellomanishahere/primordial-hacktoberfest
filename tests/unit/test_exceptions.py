"""Unit tests for custom exception hierarchy."""

import pytest
from app.core.exceptions import (
    AIServiceUnavailableException,
    EmptyDiscussionException,
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    InvalidGitHubURLException,
    PrimordialException,
    SchemaValidationException,
)


def test_base_primordial_exception():
    exc = PrimordialException(message="Custom base failure", status_code=500, error_code="TEST_ERROR", details={"k": "v"})
    assert str(exc) == "Custom base failure"
    assert exc.status_code == 500
    assert exc.error_code == "TEST_ERROR"
    assert exc.details == {"k": "v"}


def test_invalid_github_url_exception():
    exc = InvalidGitHubURLException(details={"url": "not-valid"})
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 400
    assert exc.error_code == "INVALID_GITHUB_URL"
    assert exc.details["url"] == "not-valid"


def test_github_resource_not_found_exception():
    exc = GitHubResourceNotFoundException(details={"target": "owner/repo#999"})
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 404
    assert exc.error_code == "GITHUB_RESOURCE_NOT_FOUND"


def test_github_rate_limit_exceeded_exception():
    exc = GitHubRateLimitExceededException(reset_time=1700000000)
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 429
    assert exc.error_code == "GITHUB_RATE_LIMIT_EXCEEDED"
    assert exc.details["rate_limit_reset"] == 1700000000


def test_empty_discussion_exception():
    exc = EmptyDiscussionException()
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 422
    assert exc.error_code == "EMPTY_DISCUSSION"


def test_ai_service_unavailable_exception():
    exc = AIServiceUnavailableException()
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 503
    assert exc.error_code == "AI_SERVICE_UNAVAILABLE"


def test_schema_validation_exception():
    exc = SchemaValidationException()
    assert isinstance(exc, PrimordialException)
    assert exc.status_code == 422
    assert exc.error_code == "SCHEMA_VALIDATION_ERROR"

