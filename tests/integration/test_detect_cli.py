"""Integration tests for Primordial CLI detect subcommand."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.cli import detect_decisions_url, main
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
)


@pytest.fixture
def mock_detection_result():
    return DecisionDetectionResult(
        is_decision_detected=True,
        decisions=[
            CandidateDecision(
                decision_id="dec-100-1",
                decision_statement="Adopt Undici for Fetch API",
                status=CandidateDecisionStatus.ACCEPTED,
                confidence=0.95,
                supporting_comment_ids=["0", "1"],
                repository="nodejs/node",
                entity_number=100,
                resource_type="issue",
                source_title="Implement Fetch API",
                model_name="qwen2.5:7b",
            )
        ],
        total_decisions=1,
        model_name="qwen2.5:7b",
        repository="nodejs/node",
        entity_number=100,
        resource_type="issue",
        source_url="https://github.com/nodejs/node/issues/100",
        processing_notes=["Model Deliberation Reasoning: High consensus."],
    )


@pytest.fixture
def mock_github_client():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/nodejs/node/issues/100":
            return httpx.Response(
                200,
                json={
                    "id": 100,
                    "title": "Implement Fetch API",
                    "body": "Propose native fetch support.",
                    "state": "closed",
                    "user": {"login": "dev"},
                    "created_at": "2023-01-01T00:00:00Z",
                    "html_url": "https://github.com/nodejs/node/issues/100",
                },
            )
        elif path == "/repos/nodejs/node/issues/100/comments":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "body": "We should adopt Undici for this implementation.",
                        "created_at": "2023-01-01T01:00:00Z",
                        "user": {"login": "maintainer"},
                        "html_url": "https://github.com/nodejs/node/issues/100#issuecomment-1",
                    }
                ],
            )
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, base_url="https://api.github.com")


@pytest.mark.asyncio
async def test_cli_detect_stdout(capsys, mock_github_client, mock_detection_result):
    """Verify CLI detect command writes human-readable summary and full JSON to stdout."""
    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result

        await detect_decisions_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "--- AI Decision Detection Summary ---" in captured.out
    assert "Repository: nodejs/node" in captured.out
    assert "Discussion: #100 (issue)" in captured.out
    assert "Decision Detected: YES" in captured.out
    assert "Total Candidate Decisions: 1" in captured.out
    assert "[dec-100-1] [ACCEPTED] (Confidence: 0.95)" in captured.out
    assert "Statement: Adopt Undici for Fetch API" in captured.out
    assert "--- Full JSON Output ---" in captured.out


@pytest.mark.asyncio
async def test_cli_detect_file_output(tmp_path, mock_github_client, mock_detection_result):
    """Verify CLI detect command saves JSON output to specified destination."""
    out_file = tmp_path / "decisions.json"

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result

        await detect_decisions_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(out_file),
            model="custom-model",
        )

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["is_decision_detected"] is True
    assert data["repository"] == "nodejs/node"
    assert len(data["decisions"]) == 1
    assert data["decisions"][0]["decision_statement"] == "Adopt Undici for Fetch API"


@pytest.mark.asyncio
async def test_cli_detect_invalid_url_exits(capsys):
    """Verify CLI exits with code 1 for malformed URLs."""
    with pytest.raises(SystemExit) as exc_info:
        await detect_decisions_url("https://notgithub.com/foo/bar/issues/1")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


@pytest.mark.asyncio
async def test_cli_detect_ollama_unavailable_exits(capsys, mock_github_client):
    """Verify CLI exits with code 1 and advice when Ollama is offline."""
    from app.core.exceptions import AIServiceUnavailableException

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.side_effect = AIServiceUnavailableException("Ollama offline")

        with pytest.raises(SystemExit) as exc_info:
            await detect_decisions_url("https://github.com/nodejs/node/issues/100")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "AI Service Error: Ollama offline" in captured.err
    assert "Tip: Ensure the local Ollama daemon is active" in captured.err


@pytest.mark.asyncio
async def test_cli_detect_timeout_exits(capsys, mock_github_client):
    """Verify CLI exits with code 1 when model inference times out."""
    from app.core.exceptions import AIModelTimeoutException

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.side_effect = AIModelTimeoutException("Request timed out")

        with pytest.raises(SystemExit) as exc_info:
            await detect_decisions_url("https://github.com/nodejs/node/issues/100")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "AI Timeout Error: Request timed out" in captured.err
