"""Integration tests for Primordial CLI generate-adr subcommand."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.cli import generate_adr_url
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
)
from app.evidence_verification.schemas import (
    ClaimVerificationResult,
    DecisionVerificationResult,
    EvidenceType,
    EvidenceVerificationResult,
    VerificationStatus,
)
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    ExtractedDecisionRationale,
    RationaleExtractionResult,
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
        processing_notes=[],
    )


@pytest.fixture
def mock_rationale_result():
    rationale_claim = ExtractedClaim(
        statement="Undici provides native high-performance HTTP client",
        supporting_comment_ids=["1"],
        evidence_explanation="Comment 1 supports Undici",
        confidence=0.92,
        evidence_status=EvidenceStatus.VERIFIED,
    )
    decision = ExtractedDecisionRationale(
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
        rationales=[decision],
        total_evidence_citations=1,
        processing_notes=[],
    )


@pytest.fixture
def mock_verification_result():
    claim_ver = ClaimVerificationResult(
        claim_id="dec-100-1-rationale",
        claim_type="rationale",
        claim_text="Undici provides native high-performance HTTP client",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.DIRECT,
        supporting_comment_ids=["1"],
        contradicting_comment_ids=[],
        supporting_provenance=[],
        contradicting_provenance=[],
        explanation="Corroborated by comment 1",
        confidence=0.92,
        verification_notes=[],
    )
    decision_ver = DecisionVerificationResult(
        decision_id="dec-100-1",
        decision_summary="Adopt Undici for Fetch API",
        candidate_status="accepted",
        overall_verification_status=VerificationStatus.VERIFIED,
        claim_verifications=[claim_ver],
        all_supporting_comment_ids=["1"],
        all_contradicting_comment_ids=[],
        total_claims_evaluated=1,
        verified_claims_count=1,
        partially_supported_count=0,
        contradicted_count=0,
        unsupported_count=0,
        confidence=0.92,
        verification_notes=[],
    )
    return EvidenceVerificationResult(
        is_verification_completed=True,
        repository="nodejs/node",
        entity_number=100,
        resource_type="issue",
        source_url="https://github.com/nodejs/node/issues/100",
        model_name="qwen2.5:7b",
        decisions_evaluated=1,
        verified_decisions=[decision_ver],
        total_claims_verified=1,
        total_claims_contradicted=0,
        total_claims_unsupported=0,
        processing_notes=[],
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
                    "body": "Propose native fetch support in Node.js core.",
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
# CLI Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_cli_generate_adr_stdout(
    capsys,
    mock_github_client,
    mock_detection_result,
    mock_rationale_result,
    mock_verification_result,
):
    """Verify generate-adr prints MADR 3.0.0 preview to stdout."""
    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract, \
         patch("app.cli.verify_evidence", new_callable=AsyncMock) as mock_verify:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.return_value = mock_rationale_result
        mock_verify.return_value = mock_verification_result

        await generate_adr_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "--- ADR Generation Summary ---" in captured.out
    assert "Repository:     nodejs/node" in captured.out
    assert "Total ADRs:     1" in captured.out
    assert "ADR-100-01" in captured.out
    assert "--- MADR 3.0.0 Markdown Preview ---" in captured.out
    assert "## Context and Problem Statement" in captured.out


@pytest.mark.asyncio
async def test_cli_generate_adr_file_output(
    tmp_path,
    mock_github_client,
    mock_detection_result,
    mock_rationale_result,
    mock_verification_result,
):
    """Verify generate-adr writes Markdown file to specified output path."""
    out_file = tmp_path / "test_adr.md"

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract, \
         patch("app.cli.verify_evidence", new_callable=AsyncMock) as mock_verify:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.return_value = mock_rationale_result
        mock_verify.return_value = mock_verification_result

        await generate_adr_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(out_file),
            output_format="markdown",
        )

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# ADR-100-01: Adopt Undici for Fetch API" in content
    assert "* Status: **ACCEPTED**" in content


@pytest.mark.asyncio
async def test_cli_generate_adr_json_output(
    tmp_path,
    mock_github_client,
    mock_detection_result,
    mock_rationale_result,
    mock_verification_result,
):
    """Verify generate-adr writes JSON output when format is json."""
    out_file = tmp_path / "test_adr.json"

    with patch("app.cli.GitHubClient") as mock_cls, \
         patch("app.cli.detect_decisions", new_callable=AsyncMock) as mock_detect, \
         patch("app.cli.extract_decision_rationale", new_callable=AsyncMock) as mock_extract, \
         patch("app.cli.verify_evidence", new_callable=AsyncMock) as mock_verify:

        mock_instance = mock_cls.return_value
        mock_instance.__aenter__.return_value = mock_instance
        from app.github.client import GitHubClient
        real_client = GitHubClient(client=mock_github_client)
        mock_instance.fetch_discussion.side_effect = real_client.fetch_discussion

        mock_detect.return_value = mock_detection_result
        mock_extract.return_value = mock_rationale_result
        mock_verify.return_value = mock_verification_result

        await generate_adr_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(out_file),
            output_format="json",
        )

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["total_adrs"] == 1
    assert data["adrs"][0]["adr_id"] == "ADR-100-01"
