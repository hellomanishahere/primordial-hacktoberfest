"""Integration tests for Primordial CLI verify-evidence subcommand."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.cli import verify_evidence_url
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
        statement="Undici provides native high-performance HTTP client implementation",
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
        claim_text="Undici provides native high-performance HTTP client implementation",
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
        processing_notes=["Verification successful."],
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


# ==============================================================================
# CLI Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_cli_verify_evidence_stdout(
    capsys,
    mock_github_client,
    mock_detection_result,
    mock_rationale_result,
    mock_verification_result,
):
    """Verify verify-evidence writes summary to stdout."""
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

        await verify_evidence_url("https://github.com/nodejs/node/issues/100")

    captured = capsys.readouterr()
    assert "--- Evidence Verification Summary ---" in captured.out
    assert "Repository:               nodejs/node" in captured.out
    assert "Discussion:               #100 (issue)" in captured.out
    assert "Decisions Evaluated:      1" in captured.out
    assert "Claims Verified:          1" in captured.out
    assert "dec-100-1" in captured.out


@pytest.mark.asyncio
async def test_cli_verify_evidence_file_output(
    tmp_path,
    mock_github_client,
    mock_detection_result,
    mock_rationale_result,
    mock_verification_result,
):
    """Verify verify-evidence writes JSON to specified output file."""
    out_file = tmp_path / "verification.json"

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

        await verify_evidence_url(
            "https://github.com/nodejs/node/issues/100",
            output_path=str(out_file),
            model="qwen2.5:7b",
        )

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["is_verification_completed"] is True
    assert data["repository"] == "nodejs/node"
    assert len(data["verified_decisions"]) == 1
    assert data["total_claims_verified"] == 1


@pytest.mark.asyncio
async def test_cli_verify_evidence_invalid_url_exits(capsys):
    """Verify invalid URL exits with code 1."""
    with pytest.raises(SystemExit) as exc_info:
        await verify_evidence_url("https://invalid-url.com/something")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
