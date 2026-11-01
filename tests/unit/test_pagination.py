"""Unit tests for GitHub REST API pagination and RFC 5988 Link headers."""

import httpx
import pytest
from app.core.exceptions import GitHubAPIException
from app.github.client import GitHubClient, extract_next_page_url


def test_extract_next_page_url():
    # Valid Link header with rel="next"
    header = (
        '<https://api.github.com/repositories/123/issues/456/comments?page=2&per_page=100>; rel="next", '
        '<https://api.github.com/repositories/123/issues/456/comments?page=5&per_page=100>; rel="last"'
    )
    assert extract_next_page_url(header) == "https://api.github.com/repositories/123/issues/456/comments?page=2&per_page=100"

    # Link header with only rel="prev" and rel="first" (no rel="next")
    header_no_next = (
        '<https://api.github.com/repositories/123/issues/456/comments?page=1&per_page=100>; rel="first", '
        '<https://api.github.com/repositories/123/issues/456/comments?page=4&per_page=100>; rel="prev"'
    )
    assert extract_next_page_url(header_no_next) is None

    # Empty or None header
    assert extract_next_page_url("") is None
    assert extract_next_page_url(None) is None


@pytest.mark.asyncio
async def test_pagination_single_page():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"id": 1, "body": "Comment 1"}, {"id": 2, "body": "Comment 2"}],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        items = await client.fetch_issue_comments("owner", "repo", 1)
        assert len(items) == 2
        assert items[0]["id"] == 1
        assert items[1]["id"] == 2


@pytest.mark.asyncio
async def test_pagination_multiple_pages_with_link_headers():
    requests_received = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests_received.append(str(request.url))
        if request.url.params.get("page") == "2":
            return httpx.Response(
                200,
                json=[{"id": 3, "body": "Comment 3"}],
                headers={
                    "link": '<https://api.github.com/repos/owner/repo/issues/1/comments?page=1&per_page=2>; rel="prev"'
                },
            )
        return httpx.Response(
            200,
            json=[{"id": 1, "body": "Comment 1"}, {"id": 2, "body": "Comment 2"}],
            headers={
                "link": '<https://api.github.com/repos/owner/repo/issues/1/comments?page=2&per_page=2>; rel="next"'
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        items = await client.fetch_issue_comments("owner", "repo", 1, per_page=2, max_items=10)
        assert len(items) == 3
        # Chronological order preserved
        assert [item["id"] for item in items] == [1, 2, 3]
        assert len(requests_received) == 2


@pytest.mark.asyncio
async def test_pagination_empty_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        items = await client.fetch_issue_comments("owner", "repo", 1)
        assert items == []


@pytest.mark.asyncio
async def test_pagination_missing_link_header_fallback():
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        page = request.url.params.get("page")
        if page == "1":
            # Returns exactly per_page items without Link header
            return httpx.Response(200, json=[{"id": 1}, {"id": 2}])
        elif page == "2":
            # Returns less than per_page items -> indicates last page
            return httpx.Response(200, json=[{"id": 3}])
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        items = await client.fetch_issue_comments("owner", "repo", 1, per_page=2, max_items=10)
        assert len(items) == 3
        assert [i["id"] for i in items] == [1, 2, 3]
        assert call_count == 2


@pytest.mark.asyncio
async def test_pagination_max_items_safety_ceiling():
    async def handler(request: httpx.Request) -> httpx.Response:
        # Endless items generator
        return httpx.Response(
            200,
            json=[{"id": 1}, {"id": 2}],
            headers={"link": '<https://api.github.com/repos/owner/repo/issues/1/comments?page=next>; rel="next"'},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        # Cap at max_items=4
        items = await client.fetch_issue_comments("owner", "repo", 1, per_page=2, max_items=4)
        assert len(items) == 4


@pytest.mark.asyncio
async def test_pagination_api_error_on_subsequent_page():
    async def handler(request: httpx.Request) -> httpx.Response:
        if "page=2" in str(request.url):
            return httpx.Response(500, json={"message": "Internal Server Error"})
        return httpx.Response(
            200,
            json=[{"id": 1}],
            headers={"link": '<https://api.github.com/repos/owner/repo/issues/1/comments?page=2>; rel="next"'},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        with pytest.raises(GitHubAPIException) as exc_info:
            await client.fetch_issue_comments("owner", "repo", 1, per_page=1)
        assert exc_info.value.status_code == 502
