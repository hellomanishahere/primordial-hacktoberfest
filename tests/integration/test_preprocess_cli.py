"""Integration tests for Primordial CLI preprocess subcommand."""

import json
from unittest.mock import patch
import httpx
import pytest
from app.cli import preprocess_discussion_url


@pytest.mark.asyncio
async def test_cli_preprocess_stdout(capsys):
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(
                200,
                json={
                    "id": 100,
                    "title": "Node issue",
                    "body": "Issue text",
                    "state": "open",
                    "user": {"login": "dev"},
                },
            )
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "body": "Useful technical comment",
                        "created_at": "2023-01-01T00:00:00Z",
                        "user": {"login": "bob"},
                    },
                    {
                        "id": 2,
                        "body": "+1",  # Will be filtered as reaction
                        "created_at": "2023-01-01T01:00:00Z",
                        "user": {"login": "charlie"},
                    },
                    {
                        "id": 3,
                        "body": "Automated notification",
                        "created_at": "2023-01-01T02:00:00Z",
                        "user": {"login": "dependabot[bot]"},  # Filtered as bot
                    },
                ],
            )
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    with patch("app.cli.GitHubClient") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance

        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_http_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        await preprocess_discussion_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "Ingesting and preprocessing issue from nodejs/node #100" in captured.out
    assert "Total Comments Ingested: 4" in captured.out  # description + 3 comments
    assert "Substantive Comments Retained: 2" in captured.out  # description + comment 1
    assert "Comments Removed: 2" in captured.out  # +1 and dependabot


@pytest.mark.asyncio
async def test_cli_preprocess_file_and_transcript_output(tmp_path):
    output_json = tmp_path / "cleaned.json"
    output_txt = tmp_path / "transcript.txt"

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(
                200,
                json={
                    "id": 100,
                    "title": "Node issue",
                    "body": "Issue text",
                    "state": "open",
                    "user": {"login": "dev"},
                },
            )
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "body": "Substantive discussion point",
                        "created_at": "2023-01-01T00:00:00Z",
                        "user": {"login": "bob"},
                    }
                ],
            )
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    with patch("app.cli.GitHubClient") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance

        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_http_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        await preprocess_discussion_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(output_json),
            transcript_path=str(output_txt),
        )

    # Check cleaned JSON output
    assert output_json.exists()
    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_comments"] == 2
    assert "audit" in data
    assert data["audit"]["comments_removed"] == 0

    # Check formatted transcript output
    assert output_txt.exists()
    with open(output_txt, "r", encoding="utf-8") as f:
        text = f.read()
    assert "[COMMENT ID: 0 | AUTHOR: @dev" in text
    assert "[COMMENT ID: 1 | AUTHOR: @bob" in text
    assert "Substantive discussion point" in text

