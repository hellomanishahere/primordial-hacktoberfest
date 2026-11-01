"""Unit tests for GitHub API error handling, exceptions, and security."""

import httpx
import pytest
from app.core.exceptions import (
    GitHubAPIException,
    GitHubAuthenticationException,
    GitHubForbiddenException,
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    GitHubTimeoutException,
)
from app.github.client import GitHubClient


@pytest.mark.asyncio
async def test_error_404_resource_not_found():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubResourceNotFoundException) as exc_info:
            await client.fetch_issue("owner", "nonexistent-repo", 999)
        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "GITHUB_RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_error_401_authentication_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(token="invalid_token_123", client=http_client)
        with pytest.raises(GitHubAuthenticationException) as exc_info:
            await client.fetch_repository("owner", "repo")
        assert exc_info.value.status_code == 401
        assert exc_info.value.error_code == "GITHUB_AUTHENTICATION_ERROR"
        # Ensure secret token is NEVER leaked in error messages
        assert "invalid_token_123" not in str(exc_info.value)
        assert "invalid_token_123" not in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_error_403_rate_limit_exceeded_with_header():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded for user"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1772410000"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubRateLimitExceededException) as exc_info:
            await client.fetch_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 429
        assert exc_info.value.error_code == "GITHUB_RATE_LIMIT_EXCEEDED"
        assert exc_info.value.details.get("rate_limit_reset") == 1772410000


@pytest.mark.asyncio
async def test_error_429_too_many_requests():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "Too Many Requests"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubRateLimitExceededException):
            await client.fetch_issue("owner", "repo", 1)


@pytest.mark.asyncio
async def test_error_403_forbidden_not_rate_limit():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"message": "Repository access restricted by organization owner"},
            headers={"x-ratelimit-remaining": "4900"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubForbiddenException) as exc_info:
            await client.fetch_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "GITHUB_FORBIDDEN"


@pytest.mark.asyncio
async def test_error_500_upstream_server_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "Internal Server Error"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubAPIException) as exc_info:
            await client.fetch_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 502
        assert exc_info.value.error_code == "GITHUB_API_ERROR"


@pytest.mark.asyncio
async def test_error_timeout_raised():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out after 15.0 seconds")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubTimeoutException) as exc_info:
            await client.fetch_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 504
        assert exc_info.value.error_code == "GITHUB_TIMEOUT"


@pytest.mark.asyncio
async def test_error_network_connection_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused by peer")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubAPIException) as exc_info:
            await client.fetch_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 502
        assert "network" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_error_malformed_json_during_pagination():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<!DOCTYPE html><html><body>Error</body></html>")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubAPIException) as exc_info:
            await client.fetch_issue_comments("owner", "repo", 1)
        assert "malformed json" in exc_info.value.message.lower()

