"""Custom domain and runtime exception hierarchy for Primordial."""

from typing import Any, Dict, Optional


class PrimordialException(Exception):
    """Base exception for all Primordial application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class InvalidGitHubURLException(PrimordialException):
    """Raised when an ingested URL does not match valid GitHub issue or pull request format."""

    def __init__(
        self,
        message: str = "Invalid GitHub Issue or Pull Request URL format",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_GITHUB_URL",
            details=details,
        )


class GitHubResourceNotFoundException(PrimordialException):
    """Raised when a target GitHub repository or discussion cannot be found."""

    def __init__(
        self,
        message: str = "GitHub repository, issue, or pull request not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=404,
            error_code="GITHUB_RESOURCE_NOT_FOUND",
            details=details,
        )


class GitHubRateLimitExceededException(PrimordialException):
    """Raised when GitHub API rate limits have been exhausted."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exhausted",
        reset_time: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details_payload = details.copy() if details else {}
        if reset_time is not None:
            details_payload["rate_limit_reset"] = reset_time
        super().__init__(
            message=message,
            status_code=429,
            error_code="GITHUB_RATE_LIMIT_EXCEEDED",
            details=details_payload,
        )


class GitHubAuthenticationException(PrimordialException):
    """Raised when GitHub API authentication fails (e.g. invalid GITHUB_TOKEN)."""

    def __init__(
        self,
        message: str = "GitHub API authentication failed. Verify GITHUB_TOKEN credentials.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="GITHUB_AUTHENTICATION_ERROR",
            details=details,
        )


class GitHubForbiddenException(PrimordialException):
    """Raised when access to a GitHub resource is forbidden."""

    def __init__(
        self,
        message: str = "Access to the requested GitHub resource is forbidden.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="GITHUB_FORBIDDEN",
            details=details,
        )


class GitHubTimeoutException(PrimordialException):
    """Raised when a request to the GitHub API exceeds the configured timeout."""

    def __init__(
        self,
        message: str = "GitHub API request timed out",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=504,
            error_code="GITHUB_TIMEOUT",
            details=details,
        )


class GitHubAPIException(PrimordialException):
    """Raised when the GitHub API returns an unexpected server error or malformed response."""

    def __init__(
        self,
        message: str = "GitHub API communication error",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="GITHUB_API_ERROR",
            details=details,
        )


class EmptyDiscussionException(PrimordialException):
    """Raised when an ingested discussion contains no substantive human discourse."""

    def __init__(
        self,
        message: str = "Discussion contains no human technical discourse or is empty",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="EMPTY_DISCUSSION",
            details=details,
        )


class AIServiceUnavailableException(PrimordialException):
    """Raised when the local Ollama AI daemon is offline or unreachable."""

    def __init__(
        self,
        message: str = "Local AI service (Ollama) is unavailable or unreachable",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="AI_SERVICE_UNAVAILABLE",
            details=details,
        )


class SchemaValidationException(PrimordialException):
    """Raised when an AI extraction output fails canonical Pydantic validation."""

    def __init__(
        self,
        message: str = "Extraction output failed schema validation",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="SCHEMA_VALIDATION_ERROR",
            details=details,
        )
