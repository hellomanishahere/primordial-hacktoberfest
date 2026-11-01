"""Integration tests for Primordial CLI extract-rationale subcommand."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.cli import extract_rationale_url, main
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
)
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    ExtractedDecisionRationale,
    RationaleExtractionResult,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_extraction_result():
    """A fully populated mock RationaleExtractionResult."""
    rationale_claim = ExtractedClaim(
        statement="asyncpg provides native async support with higher throughput",
        supporting_comment_ids=["1"],
        evidence_explanation="Comment 1 directly advocates asyncpg",
        confidence=0.92,
        evidence_status=EvidenceStatus.VERIFIED,
    )
    decision_rationale = ExtractedDecisionRationale(
        decision_id="dec-100-1",
        decision_summary="Adopt Undici for Fetch API",
        status="accepted",
        rationale=rationale_claim,
        supporting_arguments=[],
        opposing_arguments=[],
        rejected_alternatives=[],
        trade_offs=[],
        consequences=[],
        evidence_comment_ids=["1"],
        confidence=0.92,
        extraction_notes=[],
    )
    return RationaleExtractionResult(
        is_rationale_extracted=True,
        repository="nodejs/node",
        entity_number=100,
        resource_type="issue",
        source_url="https://github.com/nodejs/node/issues/100",
        model_name="qwen2.5:7b",
        decisions_evaluated=1,
        rationales=[decision_rationale],
        total_evidence_citations=1,
        processing_notes=["Model succeeded on first attempt."],
    )


@pytest.fixture
def mock_detection_result():
    """A DecisionDetectionResult with one accepted decision."""
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
        processing_notes=[],
    )


@pytest.fixture
def mock_github_client():
    """HTTP transport that stubs GitHub API responses for nodejs/node issue #100."""
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


# ==============================================================================
# 1. CLI extract-rationale stdout summary
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_stdout(
    capsys,
    mock_github_client,
    mock_detection_result,
    mock_extraction_result,
):
    """Verify CLI extract-rationale prints summary to stdout."""
    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.return_value = mock_extraction_result

        await extract_rationale_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "--- Rationale Extraction Summary ---" in captured.out
    assert "Repository:          nodejs/node" in captured.out
    assert "Discussion:          #100 (issue)" in captured.out
    assert "Rationale Extracted: YES" in captured.out
    assert "Decisions Evaluated: 1" in captured.out
    assert "Evidence Citations:  1" in captured.out
    assert "dec-100-1" in captured.out


# ==============================================================================
# 2. CLI extract-rationale file output
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_file_output(
    tmp_path,
    mock_github_client,
    mock_detection_result,
    mock_extraction_result,
):
    """Verify CLI extract-rationale saves well-formed JSON to the specified output file."""
    out_file = tmp_path / "rationale.json"

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.return_value = mock_extraction_result

        await extract_rationale_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(out_file),
            model="qwen2.5:7b",
        )

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["is_rationale_extracted"] is True
    assert data["repository"] == "nodejs/node"
    assert data["entity_number"] == 100
    assert len(data["rationales"]) == 1
    assert data["rationales"][0]["decision_id"] == "dec-100-1"
    assert data["rationales"][0]["status"] == "accepted"


# ==============================================================================
# 3. Invalid URL exits with code 1
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_invalid_url_exits(capsys):
    """Verify CLI exits with code 1 and prints error for invalid/non-GitHub URL."""
    with pytest.raises(SystemExit) as exc_info:
        await extract_rationale_url("https://notgithub.com/foo/bar/issues/1")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


# ==============================================================================
# 4. Ollama unavailable exits with code 1 and tip
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_ollama_unavailable_exits(
    capsys,
    mock_github_client,
    mock_detection_result,
):
    """Verify CLI exits code 1 with helpful tip when Ollama is offline."""
    from app.core.exceptions import AIServiceUnavailableException

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.side_effect = AIServiceUnavailableException("Ollama offline")

        with pytest.raises(SystemExit) as exc_info:
            await extract_rationale_url("https://github.com/nodejs/node/issues/100")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "AI Service Error: Ollama offline" in captured.err


# ==============================================================================
# 5. Timeout exits with code 1
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_timeout_exits(
    capsys,
    mock_github_client,
    mock_detection_result,
):
    """Verify CLI exits with code 1 when rationale extraction times out."""
    from app.core.exceptions import AIModelTimeoutException

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.side_effect = AIModelTimeoutException("Rationale extraction timed out")

        with pytest.raises(SystemExit) as exc_info:
            await extract_rationale_url("https://github.com/nodejs/node/issues/100")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "AI Timeout Error:" in captured.err


# ==============================================================================
# 6. No decisions detected: exits cleanly with informational message
# ==============================================================================
@pytest.mark.asyncio
async def test_cli_extract_rationale_no_decisions_clean_exit(
    capsys,
    mock_github_client,
):
    """Verify CLI exits cleanly (code 0) with informational message when no decisions detected."""
    no_decisions = DecisionDetectionResult(
        is_decision_detected=False,
        decisions=[],
        total_decisions=0,
        model_name="qwen2.5:7b",
        repository="nodejs/node",
        entity_number=100,
        resource_type="issue",
        source_url="https://github.com/nodejs/node/issues/100",
        processing_notes=[],
    )
    no_rationale = RationaleExtractionResult(
        is_rationale_extracted=False,
        repository="nodejs/node",
        entity_number=100,
        resource_type="issue",
        source_url="https://github.com/nodejs/node/issues/100",
        model_name="qwen2.5:7b",
        decisions_evaluated=0,
        rationales=[],
        total_evidence_citations=0,
        processing_notes=["No candidate decisions detected in discussion. Skipping rationale extraction."],
    )

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = no_decisions
        mock_extract.return_value = no_rationale

        # Should NOT raise SystemExit
        await extract_rationale_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "Rationale Extracted: NO" in captured.out


# ==============================================================================
# 7. Existing fetch, preprocess, detect commands unaffected (regression)
# ==============================================================================
def test_cli_existing_commands_unaffected():
    """Verify that fetch, preprocess, detect, and extract-rationale all appear in CLI help."""
    import subprocess
    import sys
    from pathlib import Path

    result = subprocess.run(
        [sys.executable, "backend/app/cli.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0
    assert "fetch" in result.stdout
    assert "preprocess" in result.stdout
    assert "detect" in result.stdout
    assert "extract-rationale" in result.stdout
    assert "extract" in result.stdout

