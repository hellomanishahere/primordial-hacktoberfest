"""Unit tests for GitHub REST API Client."""

import httpx
import pytest
from app.github.client import GitHubClient
from app.github.parser import parse_github_url


@pytest.mark.asyncio
async def test_fetch_issue_successful():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/nodejs/node/issues/100"
        assert request.headers.get("accept") == "application/vnd.github.v3+json"
        assert "Primordial" in request.headers.get("user-agent", "")
        return httpx.Response(
            200,
            json={
                "id": 100,
                "number": 100,
                "title": "Bug in HTTP parser",
                "body": "Null pointer on empty buffer",
                "state": "open",
                "user": {"login": "alice"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        data = await client.fetch_issue("nodejs", "node", 100)
        assert data["id"] == 100
        assert data["title"] == "Bug in HTTP parser"
        assert data["user"]["login"] == "alice"


@pytest.mark.asyncio
async def test_fetch_pull_request_successful():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/nodejs/node/pulls/41749"
        return httpx.Response(
            200,
            json={
                "id": 41749,
                "number": 41749,
                "title": "Adopt Undici as built-in fetch",
                "body": "Proposal to integrate undici into Node.js core",
                "state": "closed",
                "merged": True,
                "user": {"login": "mcollina"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        data = await client.fetch_pull_request("nodejs", "node", 41749)
        assert data["number"] == 41749
        assert data["merged"] is True
        assert data["user"]["login"] == "mcollina"


@pytest.mark.asyncio
async def test_fetch_issue_comments_successful():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/nodejs/node/issues/41749/comments"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 1034981,
                    "user": {"login": "mcollina"},
                    "body": "Undici outperforms node-fetch in benchmarks.",
                    "created_at": "2022-02-03T14:22:10Z",
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        comments = await client.fetch_issue_comments("nodejs", "node", 41749)
        assert len(comments) == 1
        assert comments[0]["id"] == 1034981


@pytest.mark.asyncio
async def test_fetch_pull_request_comments_successful():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/nodejs/node/pulls/41749/comments"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 888123,
                    "user": {"login": "jasnell"},
                    "body": "Ensure stream cleanup on error.",
                    "path": "lib/fetch.js",
                    "diff_hunk": "@@ -1,5 +1,5 @@",
                    "created_at": "2022-02-03T15:00:00Z",
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        comments = await client.fetch_pull_request_comments("nodejs", "node", 41749)
        assert len(comments) == 1
        assert comments[0]["id"] == 888123
        assert comments[0]["path"] == "lib/fetch.js"


@pytest.mark.asyncio
async def test_fetch_pull_request_reviews_successful():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/nodejs/node/pulls/41749/reviews"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 777001,
                    "user": {"login": "ronag"},
                    "state": "APPROVED",
                    "body": "LGTM, benchmarks look solid.",
                    "submitted_at": "2022-02-03T16:00:00Z",
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        reviews = await client.fetch_pull_request_reviews("nodejs", "node", 41749)
        assert len(reviews) == 1
        assert reviews[0]["id"] == 777001
        assert reviews[0]["state"] == "APPROVED"


@pytest.mark.asyncio
async def test_auth_header_present_when_token_configured():
    captured_auth = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_auth.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"id": 1, "name": "test-repo"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(token="ghp_test_secret_token", client=http_client)
        await client.fetch_repository("owner", "test-repo")

    assert len(captured_auth) == 1
    assert captured_auth[0] == "Bearer ghp_test_secret_token"


@pytest.mark.asyncio
async def test_auth_header_omitted_when_token_absent():
    captured_auth = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_auth.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"id": 1, "name": "public-repo"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(token=None, client=http_client)
        await client.fetch_repository("owner", "public-repo")

    assert len(captured_auth) == 1
    assert captured_auth[0] is None


@pytest.mark.asyncio
async def test_fetch_full_discussion_for_pull_request():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/pulls/41749":
            return httpx.Response(200, json={"id": 41749, "title": "Fetch PR", "body": "PR description"})
        elif path == "/repos/nodejs/node/issues/41749/comments":
            return httpx.Response(200, json=[{"id": 1, "body": "conversation comment"}])
        elif path == "/repos/nodejs/node/pulls/41749/comments":
            return httpx.Response(200, json=[{"id": 2, "body": "diff review comment"}])
        elif path == "/repos/nodejs/node/pulls/41749/reviews":
            return httpx.Response(200, json=[{"id": 3, "body": "review summary"}])
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        target = parse_github_url("https://github.com/nodejs/node/pull/41749")
        data = await client.fetch_discussion(target)

        assert data["target"] == target
        assert data["metadata"]["title"] == "Fetch PR"
        assert len(data["conversation_comments"]) == 1
        assert len(data["review_comments"]) == 1
        assert len(data["reviews"]) == 1


@pytest.mark.asyncio
async def test_fetch_full_discussion_for_issue():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(200, json={"id": 100, "title": "Issue title", "body": "Issue description"})
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(200, json=[{"id": 1, "body": "conversation comment"}])
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as http_client:
        client = GitHubClient(client=http_client)
        target = parse_github_url("https://github.com/nodejs/node/issues/100")
        data = await client.fetch_discussion(target)

        assert data["target"] == target
        assert data["metadata"]["title"] == "Issue title"
        assert len(data["conversation_comments"]) == 1
        # Issues should have empty review lists without making calls
        assert data["review_comments"] == []
        assert data["reviews"] == []

