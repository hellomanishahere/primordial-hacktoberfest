"""Async GitHub REST API Client with rate limiting, RFC 5988 pagination, and error translation."""

import json
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.exceptions import (
    GitHubAPIException,
    GitHubAuthenticationException,
    GitHubForbiddenException,
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    GitHubTimeoutException,
)
from app.core.logging import get_logger
from app.github.parser import GitHubTarget
from app.github.router import ExecutionPlan, create_execution_plan

logger = get_logger(__name__)


def extract_next_page_url(link_header: Optional[str]) -> Optional[str]:
    """
    Extracts the URL with rel="next" from an RFC 5988 Link header.

    Args:
        link_header: Raw Link header string from HTTP response.

    Returns:
        Next page URL if present, otherwise None.
    """
    if not link_header:
        return None

    for item in link_header.split(","):
        segments = item.strip().split(";")
        if len(segments) >= 2:
            url_part = segments[0].strip()
            params = [s.strip() for s in segments[1:]]
            if any('rel="next"' in p for p in params):
                if url_part.startswith("<") and url_part.endswith(">"):
                    return url_part[1:-1]
    return None


class GitHubClient:
    """Async client for GitHub REST API v3."""

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout: float = 15.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # Priority: explicit token argument > environment settings
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.timeout = timeout
        self._external_client = client
        self._internal_client: Optional[httpx.AsyncClient] = None

    def _build_headers(self) -> Dict[str, str]:
        """Constructs standardized GitHub API headers without exposing credentials."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Primordial-Decision-Intelligence/2.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the active httpx.AsyncClient instance."""
        if self._external_client is not None:
            return self._external_client

        if self._internal_client is None or self._internal_client.is_closed:
            self._internal_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._build_headers(),
                timeout=self.timeout,
            )
        return self._internal_client

    async def close(self) -> None:
        """Closes internal HTTP client if managed by this instance."""
        if self._internal_client is not None and not self._internal_client.is_closed:
            await self._internal_client.aclose()
            self._internal_client = None

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _handle_error_response(self, response: httpx.Response, endpoint: str) -> None:
        """Translates HTTP error status codes into domain exceptions."""
        status_code = response.status_code

        # Rate Limit Inspection: 429 or 403 with x-ratelimit-remaining == 0
        remaining = response.headers.get("x-ratelimit-remaining")
        reset_epoch = response.headers.get("x-ratelimit-reset")
        reset_time = int(reset_epoch) if reset_epoch and reset_epoch.isdigit() else None

        is_rate_limit = (
            status_code == 429
            or (status_code == 403 and remaining == "0")
            or "API rate limit exceeded" in response.text
        )

        if is_rate_limit:
            raise GitHubRateLimitExceededException(
                message="GitHub API rate limit exhausted",
                reset_time=reset_time,
                details={"endpoint": endpoint, "rate_limit_reset": reset_time},
            )

        if status_code == 404:
            raise GitHubResourceNotFoundException(
                message=f"GitHub resource not found at endpoint: {endpoint}",
                details={"endpoint": endpoint},
            )

        if status_code == 401:
            raise GitHubAuthenticationException(
                message="GitHub API authentication failed. Verify GITHUB_TOKEN credentials.",
                details={"endpoint": endpoint},
            )

        if status_code == 403:
            raise GitHubForbiddenException(
                message="Access to the requested GitHub resource is forbidden.",
                details={"endpoint": endpoint},
            )

        if status_code >= 500:
            raise GitHubAPIException(
                message=f"GitHub API upstream error: HTTP {status_code}",
                status_code=502,
                details={"endpoint": endpoint, "status_code": status_code},
            )

        raise GitHubAPIException(
            message=f"GitHub API request failed with HTTP {status_code}",
            status_code=status_code,
            details={"endpoint": endpoint, "status_code": status_code},
        )

    async def _request(
        self,
        method: str,
        endpoint_or_url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Performs HTTP request with error catching for timeouts and network failures."""
        client = await self._get_client()

        # Determine if endpoint is full URL or relative path
        if endpoint_or_url.startswith("http://") or endpoint_or_url.startswith("https://"):
            url = endpoint_or_url
        else:
            url = f"{self.base_url}{endpoint_or_url}" if not endpoint_or_url.startswith(self.base_url) else endpoint_or_url

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                headers=self._build_headers(),
            )
        except httpx.TimeoutException as exc:
            logger.warning("GitHub request timed out for %s: %s", endpoint_or_url, exc)
            raise GitHubTimeoutException(
                message="GitHub API request timed out",
                details={"endpoint": endpoint_or_url},
            ) from exc
        except (httpx.NetworkError, httpx.ConnectError) as exc:
            logger.warning("Network failure connecting to GitHub API for %s: %s", endpoint_or_url, exc)
            raise GitHubAPIException(
                message="Failed to connect to GitHub API network",
                status_code=502,
                details={"endpoint": endpoint_or_url},
            ) from exc

        if not response.is_success:
            self._handle_error_response(response, endpoint_or_url)

        return response

    async def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_items: int = 250,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Paginates through GitHub collection endpoints using RFC 5988 Link headers and safety ceilings.

        Args:
            endpoint: Relative path endpoint (e.g. /repos/owner/repo/issues/1/comments)
            params: Query parameters.
            max_items: Upper limit of items to ingest to prevent memory exhaustion or rate depletion.
            per_page: Items requested per page (GitHub max is 100).

        Returns:
            List of collected items preserving chronological order.
        """
        all_items: List[Dict[str, Any]] = []
        query_params = dict(params or {})
        query_params.setdefault("per_page", per_page)
        query_params.setdefault("page", 1)

        current_url: Optional[str] = endpoint
        page_counter = 1
        max_pages = max(1, (max_items + per_page - 1) // per_page + 2)
        seen_urls = set()

        while current_url and len(all_items) < max_items and page_counter <= max_pages:
            seen_urls.add(current_url)

            # Pass query params only on the initial relative request; Link header URLs already contain params
            call_params = query_params if current_url == endpoint else None
            response = await self._request("GET", current_url, params=call_params)

            try:
                page_data = response.json()
            except json.JSONDecodeError as exc:
                raise GitHubAPIException(
                    message="Malformed JSON received from GitHub API during pagination",
                    status_code=502,
                    details={"endpoint": current_url},
                ) from exc

            if not isinstance(page_data, list):
                # Endpoint returned an unexpected non-list body
                break

            if not page_data:
                # Empty page returned; end of collection
                break

            for item in page_data:
                all_items.append(item)
                if len(all_items) >= max_items:
                    break

            # Check for RFC 5988 Link header for rel="next"
            link_header = response.headers.get("link")
            next_url = extract_next_page_url(link_header)

            if next_url and next_url not in seen_urls:
                current_url = next_url
            elif not link_header and len(page_data) == query_params.get("per_page", per_page):
                # Fallback: increment page query parameter if Link header was omitted by a mock or proxy
                page_counter += 1
                query_params["page"] = page_counter
                current_url = endpoint
            else:
                current_url = None

            page_counter += 1

        return all_items

    async def fetch_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetches top-level repository details."""
        endpoint = f"/repos/{owner}/{repo}"
        response = await self._request("GET", endpoint)
        return response.json()

    async def fetch_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetches Issue metadata and initial description."""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}"
        response = await self._request("GET", endpoint)
        return response.json()

    async def fetch_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetches Pull Request metadata and initial description."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}"
        response = await self._request("GET", endpoint)
        return response.json()

    async def fetch_issue_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        per_page: int = 100,
        max_items: int = 250,
    ) -> List[Dict[str, Any]]:
        """Fetches conversational comments for an issue or pull request."""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        return await self._paginate(endpoint, max_items=max_items, per_page=per_page)

    async def fetch_pull_request_comments(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
        max_items: int = 250,
    ) -> List[Dict[str, Any]]:
        """Fetches inline diff review comments for a pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/comments"
        return await self._paginate(endpoint, max_items=max_items, per_page=per_page)

    async def fetch_pull_request_reviews(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
        max_items: int = 250,
    ) -> List[Dict[str, Any]]:
        """Fetches review summaries for a pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        return await self._paginate(endpoint, max_items=max_items, per_page=per_page)

    async def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
        max_items: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetches modified files list and diff patches for a pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/files"
        return await self._paginate(endpoint, max_items=max_items, per_page=per_page)

    async def fetch_discussion(
        self,
        target: GitHubTarget,
        max_comments: int = 250,
    ) -> Dict[str, Any]:
        """
        Coordinates full data ingestion for a GitHub target according to its execution plan.

        Args:
            target: Validated GitHub target.
            max_comments: Upper ceiling of total comments to fetch per endpoint.

        Returns:
            Dictionary containing raw metadata, conversation comments, review comments, and reviews.
        """
        plan: ExecutionPlan = create_execution_plan(target)
        owner = target.owner
        repo = target.repo
        number = target.entity_number

        if plan.is_pull_request:
            metadata = await self.fetch_pull_request(owner, repo, number)
            conversation_comments = await self.fetch_issue_comments(owner, repo, number, max_items=max_comments)
            review_comments = await self.fetch_pull_request_comments(owner, repo, number, max_items=max_comments)
            reviews = await self.fetch_pull_request_reviews(owner, repo, number, max_items=max_comments)
        else:
            metadata = await self.fetch_issue(owner, repo, number)
            conversation_comments = await self.fetch_issue_comments(owner, repo, number, max_items=max_comments)
            review_comments = []
            reviews = []

        return {
            "target": target,
            "metadata": metadata,
            "conversation_comments": conversation_comments,
            "review_comments": review_comments,
            "reviews": reviews,
        }

