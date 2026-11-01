"""Comprehensive unit tests for Module 8: ADR/MADR Generation."""

from datetime import datetime, timezone
import json
import os
import pytest

from app.adr_generation.exporter import export_adr_to_file, export_all_adrs
from app.adr_generation.generator import ADRGenerator, generate_adrs
from app.adr_generation.schemas import (
    ADRAlternative,
    ADRDocument,
    ADREvidenceRef,
    ADRGenerationResult,
    ADRStatus,
)
from app.adr_generation.templates import render_madr_markdown
from app.domain.entities import CommentType
from app.evidence_verification.schemas import (
    ClaimVerificationResult,
    CommentProvenance,
    DecisionVerificationResult,
    EvidenceType,
    EvidenceVerificationResult,
    VerificationStatus,
)
from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    PreprocessingAudit,
)


def make_comment(
    comment_id: str,
    author: str = "alice",
    body: str = "Technical discussion comment",
) -> CleanedDiscussionComment:
    return CleanedDiscussionComment(
        id=comment_id,
        comment_type=CommentType.CONVERSATION,
        author=author,
        author_association="MEMBER",
        body=body,
        created_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        html_url=f"https://github.com/org/repo/pull/123#issuecomment-{comment_id}",
    )


def make_thread(
    title: str = "Adopt Connection Pooling",
    body: str = "We need connection pooling for high concurrent query performance.",
) -> CleanedDiscussionThread:
    comments = [
        make_comment("0", "alice", body),
        make_comment("101", "bob", "LGTM, let's adopt asyncpg pooling"),
        make_comment("102", "charlie", "psycopg2 rejected due to sync blocking"),
    ]
    audit = PreprocessingAudit(
        total_comments_input=len(comments),
        substantive_comments_retained=len(comments),
        comments_removed=0,
        is_empty=False,
    )
    return CleanedDiscussionThread(
        repository_owner="org",
        repository_name="repo",
        entity_number=123,
        resource_type="pull_request",
        title=title,
        body=body,
        state="closed",
        author="alice",
        created_at=datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
        html_url="https://github.com/org/repo/pull/123",
        comments=comments,
        audit=audit,
        estimated_tokens=300,
    )


def make_verification_result(
    num_decisions: int = 1,
    include_contradiction: bool = False,
    include_alternative: bool = True,
    status: str = "accepted",
) -> EvidenceVerificationResult:
    vdec_list = []
    for i in range(num_decisions):
        dec_id = f"dec-123-{i+1}"
        claims = [
            ClaimVerificationResult(
                claim_id=f"{dec_id}-rationale",
                claim_type="rationale",
                claim_text="asyncpg provides native async support with higher throughput",
                status=VerificationStatus.VERIFIED,
                evidence_type=EvidenceType.DIRECT,
                supporting_comment_ids=["101"],
                contradicting_comment_ids=[],
                supporting_provenance=[
                    CommentProvenance(
                        comment_id="101",
                        author="bob",
                        author_association="MEMBER",
                        created_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                        html_url="https://github.com/org/repo/pull/123#issuecomment-101",
                        body_snippet="LGTM, let's adopt asyncpg pooling",
                    )
                ],
                contradicting_provenance=[],
                explanation="Corroborated by comment 101",
                confidence=0.92,
                verification_notes=[],
            ),
            ClaimVerificationResult(
                claim_id=f"{dec_id}-tradeoff-0",
                claim_type="trade_off",
                claim_text="Requires migrating query syntax",
                status=VerificationStatus.VERIFIED,
                evidence_type=EvidenceType.DIRECT,
                supporting_comment_ids=["0"],
                contradicting_comment_ids=[],
                supporting_provenance=[
                    CommentProvenance(
                        comment_id="0",
                        author="alice",
                        author_association="MEMBER",
                        created_at=datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                        html_url="https://github.com/org/repo/pull/123",
                        body_snippet="We need connection pooling",
                    )
                ],
                contradicting_provenance=[],
                explanation="From PR description",
                confidence=0.85,
                verification_notes=[],
            ),
        ]

        if include_alternative:
            claims.append(
                ClaimVerificationResult(
                    claim_id=f"{dec_id}-alt-0",
                    claim_type="rejected_alternative",
                    claim_text="psycopg2 synchronous adapter",
                    status=VerificationStatus.VERIFIED,
                    evidence_type=EvidenceType.DIRECT,
                    supporting_comment_ids=["102"],
                    contradicting_comment_ids=[],
                    supporting_provenance=[
                        CommentProvenance(
                            comment_id="102",
                            author="charlie",
                            author_association="MEMBER",
                            created_at=datetime(2023, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
                            html_url="https://github.com/org/repo/pull/123#issuecomment-102",
                            body_snippet="psycopg2 rejected due to sync blocking",
                        )
                    ],
                    contradicting_provenance=[],
                    explanation="Rejected because it causes sync event loop blocking",
                    confidence=0.90,
                    verification_notes=[],
                )
            )

        if include_contradiction:
            claims.append(
                ClaimVerificationResult(
                    claim_id=f"{dec_id}-opp-0",
                    claim_type="opposing_argument",
                    claim_text="Potential resource starvation under misconfiguration",
                    status=VerificationStatus.CONTRADICTED,
                    evidence_type=EvidenceType.INFERRED,
                    supporting_comment_ids=[],
                    contradicting_comment_ids=["103"],
                    supporting_provenance=[],
                    contradicting_provenance=[
                        CommentProvenance(
                            comment_id="103",
                            author="david",
                            author_association="MEMBER",
                            created_at=datetime(2023, 1, 15, 15, 0, 0, tzinfo=timezone.utc),
                            html_url="https://github.com/org/repo/pull/123#issuecomment-103",
                            body_snippet="I object, this causes resource starvation",
                        )
                    ],
                    explanation="Challenged by comment 103",
                    confidence=0.8,
                    verification_notes=[],
                )
            )

        vdec_list.append(
            DecisionVerificationResult(
                decision_id=dec_id,
                decision_summary=f"Adopt asyncpg connection pooling ({i+1})",
                candidate_status=status,
                overall_verification_status=VerificationStatus.VERIFIED,
                claim_verifications=claims,
                all_supporting_comment_ids=["0", "101", "102"],
                all_contradicting_comment_ids=["103"] if include_contradiction else [],
                total_claims_evaluated=len(claims),
                verified_claims_count=len(claims) - (1 if include_contradiction else 0),
                partially_supported_count=0,
                contradicted_count=1 if include_contradiction else 0,
                unsupported_count=0,
                confidence=0.9,
                verification_notes=[],
            )
        )

    return EvidenceVerificationResult(
        is_verification_completed=True,
        repository="org/repo",
        entity_number=123,
        resource_type="pull_request",
        source_url="https://github.com/org/repo/pull/123",
        model_name="qwen2.5:7b",
        decisions_evaluated=len(vdec_list),
        verified_decisions=vdec_list,
        total_claims_verified=len(vdec_list) * 2,
        total_claims_contradicted=1 if include_contradiction else 0,
        total_claims_unsupported=0,
        processing_notes=[],
    )


# ==============================================================================
# Unit tests
# ==============================================================================

def test_1_complete_adr_generation():
    """Verify ADRGenerator creates complete ADRDocument with required fields."""
    thread = make_thread()
    v_result = make_verification_result()

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)

    assert adr_res.total_adrs == 1
    doc = adr_res.adrs[0]
    assert doc.adr_id == "ADR-123-01"
    assert "Adopt asyncpg connection pooling" in doc.title
    assert doc.status == ADRStatus.ACCEPTED
    assert doc.repository == "org/repo"
    assert doc.entity_number == 123
    assert len(doc.supporting_evidence) >= 1
    assert len(doc.considered_alternatives) == 1
    assert "psycopg2" in doc.considered_alternatives[0].title


def test_2_missing_context_handled_gracefully():
    """Verify that empty/missing body or title falls back to 'Not established in discussion'."""
    thread = make_thread(title="", body="")
    v_result = make_verification_result()

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)

    doc = adr_res.adrs[0]
    assert doc.context == "Not established in discussion."
    assert doc.problem_statement == "Not established in discussion."


def test_3_rejected_alternatives_preserved_with_reasons():
    """Verify that rejected alternatives and reasons are faithfully transferred."""
    thread = make_thread()
    v_result = make_verification_result(include_alternative=True)

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)

    doc = adr_res.adrs[0]
    assert len(doc.considered_alternatives) == 1
    alt = doc.considered_alternatives[0]
    assert "psycopg2" in alt.title
    assert "sync event loop blocking" in alt.rejection_reason
    assert len(alt.evidence_refs) == 1
    assert alt.evidence_refs[0].comment_id == "102"


def test_4_multiple_decisions_create_multiple_adrs():
    """Verify that 2 verified decisions generate 2 distinct ADRs with stable incrementing IDs."""
    thread = make_thread()
    v_result = make_verification_result(num_decisions=2)

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)

    assert adr_res.total_adrs == 2
    assert adr_res.adrs[0].adr_id == "ADR-123-01"
    assert adr_res.adrs[1].adr_id == "ADR-123-02"


def test_5_contradictory_evidence_section():
    """Verify contradictory evidence is captured in contradictory_evidence field."""
    thread = make_thread()
    v_result = make_verification_result(include_contradiction=True)

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)

    doc = adr_res.adrs[0]
    assert len(doc.contradictory_evidence) == 1
    assert doc.contradictory_evidence[0].comment_id == "103"
    assert doc.contradictory_evidence[0].author == "david"


def test_6_madr_markdown_rendering():
    """Verify render_madr_markdown produces MADR 3.0.0 sections."""
    thread = make_thread()
    v_result = make_verification_result(include_alternative=True, include_contradiction=True)

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)
    doc = adr_res.adrs[0]

    md = render_madr_markdown(doc)

    assert f"# {doc.adr_id}: {doc.title}" in md
    assert "* Status: **ACCEPTED**" in md
    assert "## Context and Problem Statement" in md
    assert "## Decision Drivers" in md
    assert "## Considered Options" in md
    assert "## Decision Outcome" in md
    assert "### Positive Consequences" in md
    assert "### Architectural Trade-offs" in md
    assert "## Supporting Evidence" in md
    assert "## Contradictory Evidence & Objections" in md
    assert "## Original GitHub Discussion" in md


def test_7_json_serialization():
    """Verify to_dict() produces JSON-serializable dictionary."""
    thread = make_thread()
    v_result = make_verification_result()

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)
    data = adr_res.to_dict()

    assert data["total_adrs"] == 1
    assert isinstance(data["adrs"], list)
    assert data["adrs"][0]["adr_id"] == "ADR-123-01"
    assert data["adrs"][0]["status"] == "accepted"
    # Ensure it's json dumpable
    dumped = json.dumps(data)
    assert "ADR-123-01" in dumped


def test_8_stable_file_slug():
    """Verify generate_slug produces predictable clean filename."""
    slug = ADRDocument.generate_slug("ADR-0001", "Adopt Undici for Fetch API!")
    assert slug == "adr-0001-adopt-undici-for-fetch-api"


def test_9_exporter_writes_markdown_and_json(tmp_path):
    """Verify export_adr_to_file and export_all_adrs write valid files to disk."""
    thread = make_thread()
    v_result = make_verification_result()

    generator = ADRGenerator()
    adr_res = generator.generate(thread=thread, verification_result=v_result)
    doc = adr_res.adrs[0]

    # Markdown export
    md_file = tmp_path / "test.md"
    export_adr_to_file(doc, str(md_file), format="markdown")
    assert md_file.exists()
    assert "# ADR-123-01" in md_file.read_text(encoding="utf-8")

    # JSON export
    json_file = tmp_path / "test.json"
    export_adr_to_file(doc, str(json_file), format="json")
    assert json_file.exists()
    json_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert json_data["adr_id"] == "ADR-123-01"

    # Export all
    all_dir = tmp_path / "all_adrs"
    exported = export_all_adrs(adr_res, str(all_dir), format="markdown")
    assert len(exported) == 1
    assert os.path.exists(exported[0])


def test_10_status_mapping():
    """Verify candidate statuses (proposed, rejected, deferred, unclear) map properly."""
    thread = make_thread()
    for cand_status, expected_adr_status in [
        ("proposed", ADRStatus.PROPOSED),
        ("rejected", ADRStatus.REJECTED),
        ("deferred", ADRStatus.DEFERRED),
        ("unclear", ADRStatus.UNCLEAR),
        ("accepted", ADRStatus.ACCEPTED),
    ]:
        v_res = make_verification_result(status=cand_status)
        doc = ADRGenerator().generate(thread, v_res).adrs[0]
        assert doc.status == expected_adr_status

