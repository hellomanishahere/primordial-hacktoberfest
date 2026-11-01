"""Integration tests for Primordial CLI fetch subcommand."""

import json
from unittest.mock import patch
import httpx
import pytest
from app.cli import fetch_and_normalize_url


@pytest.mark.asyncio
async def test_cli_fetch_and_normalize_stdout(capsys):
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(200, json={"id": 100, "title": "Node issue", "body": "Issue text", "state": "open", "user": {"login": "dev"}})
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(200, json=[{"id": 1, "body": "A comment", "created_at": "2023-01-01T00:00:00Z", "user": {"login": "bob"}}])
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    with patch("app.cli.GitHubClient") as mock_cls:
        # Context manager returns mock client
        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance

        # Call real fetch_discussion logic by wrapping with real GitHubClient instance using mock_http_client
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_http_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        await fetch_and_normalize_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "Ingesting issue from nodejs/node #100" in captured.out
    assert "Title: Node issue" in captured.out
    assert "Total Comments Ingested: 2" in captured.out


@pytest.mark.asyncio
async def test_cli_fetch_and_normalize_file_output(tmp_path):
    output_file = tmp_path / "normalized.json"

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(200, json={"id": 100, "title": "Node issue", "body": "Issue text", "state": "open", "user": {"login": "dev"}})
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(200, json=[])
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    with patch("app.cli.GitHubClient") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_http_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        await fetch_and_normalize_url("https://github.com/nodejs/node/issues/100", output_path=str(output_file))

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["title"] == "Node issue"
    assert data["total_comments"] == 1


@pytest.mark.asyncio
async def test_cli_fetch_invalid_url_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        await fetch_and_normalize_url("https://gitlab.com/invalid/url")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Unsupported hostname" in captured.err


@pytest.mark.asyncio
async def test_cli_fetch_404_exits(capsys):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    with patch("app.cli.GitHubClient") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_http_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        with pytest.raises(SystemExit) as exc_info:
            await fetch_and_normalize_url("https://github.com/owner/nonexistent/issues/1")
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Not Found:" in captured.err

