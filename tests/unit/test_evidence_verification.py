"""Comprehensive unit tests for Module 7: Evidence Verification."""

from datetime import datetime, timezone
from typing import List, Optional
import pytest

from app.domain.entities import CommentType
from app.evidence_verification.rules import (
    extract_provenance,
    tokenize_statement,
    verify_claim_deterministically,
)
from app.evidence_verification.schemas import (
    EvidenceType,
    VerificationStatus,
)
from app.evidence_verification.verifier import (
    EvidenceVerifier,
    verify_evidence,
)
from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    PreprocessingAudit,
)
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    ExtractedDecisionRationale,
    RationaleExtractionResult,
    RejectedAlternative,
)


def make_comment(
    comment_id: str,
    author: str = "alice",
    body: str = "Technical discussion comment",
    comment_type: CommentType = CommentType.CONVERSATION,
) -> CleanedDiscussionComment:
    return CleanedDiscussionComment(
        id=comment_id,
        comment_type=comment_type,
        author=author,
        author_association="MEMBER",
        body=body,
        created_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        html_url=f"https://github.com/org/repo/pull/123#issuecomment-{comment_id}",
    )


def make_thread(
    comments: Optional[List[CleanedDiscussionComment]] = None,
    is_empty: bool = False,
) -> CleanedDiscussionThread:
    cmt_list = comments if comments is not None else [
        make_comment("0", "alice", "PR Description: Propose asyncpg connection pooling for PostgreSQL access"),
        make_comment("101", "bob", "LGTM, let's adopt asyncpg pooling. It provides high throughput and native async support."),
        make_comment("102", "charlie", "We considered psycopg2 but rejected it because it causes sync blocking in the event loop."),
    ]
    audit = PreprocessingAudit(
        total_comments_input=len(cmt_list),
        substantive_comments_retained=len(cmt_list),
        comments_removed=0,
        is_empty=is_empty or len(cmt_list) == 0,
    )
    return CleanedDiscussionThread(
        repository_owner="org",
        repository_name="repo",
        entity_number=123,
        resource_type="pull_request",
        title="Adopt Connection Pooling",
        body="PR body",
        state="closed",
        author="alice",
        created_at=datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
        html_url="https://github.com/org/repo/pull/123",
        comments=cmt_list,
        audit=audit,
        estimated_tokens=500,
    )


def make_rationale_result(
    rationale_ids: Optional[List[str]] = None,
    supporting_ids: Optional[List[str]] = None,
    opposing_ids: Optional[List[str]] = None,
    alternative_ids: Optional[List[str]] = None,
    tradeoff_ids: Optional[List[str]] = None,
    consequence_ids: Optional[List[str]] = None,
    alt_statement: str = "psycopg2 synchronous adapter",
    alt_rejection: str = "Causes sync blocking in the event loop",
    is_extracted: bool = True,
) -> RationaleExtractionResult:
    decision = ExtractedDecisionRationale(
        decision_id="dec-123-1",
        decision_summary="Adopt asyncpg connection pooling",
        status="accepted",
        rationale=ExtractedClaim(
            statement="asyncpg provides native async support with higher throughput",
            supporting_comment_ids=rationale_ids if rationale_ids is not None else ["101"],
            evidence_explanation="Comment 101 discusses asyncpg throughput",
            confidence=0.92,
            evidence_status=EvidenceStatus.VERIFIED,
        ),
        supporting_arguments=[
            ExtractedClaim(
                statement="Connection pooling reduces database contention",
                supporting_comment_ids=supporting_ids if supporting_ids is not None else ["0", "101"],
                evidence_explanation="Comment 0 and 101 support pooling",
                confidence=0.88,
                evidence_status=EvidenceStatus.VERIFIED,
            )
        ] if supporting_ids is not False else [],
        opposing_arguments=[
            ExtractedClaim(
                statement="Concerns raised regarding asyncpg complexity",
                supporting_comment_ids=opposing_ids if opposing_ids else [],
                evidence_explanation="Opposition",
                confidence=0.7,
                evidence_status=EvidenceStatus.VERIFIED,
            )
        ] if opposing_ids else [],
        rejected_alternatives=[
            RejectedAlternative(
                statement=alt_statement,
                rejection_reason=alt_rejection,
                supporting_comment_ids=alternative_ids if alternative_ids is not None else ["102"],
                evidence_explanation="Comment 102 rejected psycopg2",
                confidence=0.9,
                evidence_status=EvidenceStatus.VERIFIED,
            )
        ] if alternative_ids is not False else [],
        trade_offs=[
            ExtractedClaim(
                statement="Requires updating all query call sites",
                supporting_comment_ids=tradeoff_ids if tradeoff_ids is not None else ["0"],
                evidence_explanation="PR description",
                confidence=0.8,
                evidence_status=EvidenceStatus.VERIFIED,
            )
        ] if tradeoff_ids is not False else [],
        consequences=[
            ExtractedClaim(
                statement="Higher throughput under concurrent load",
                supporting_comment_ids=consequence_ids if consequence_ids is not None else ["101"],
                evidence_explanation="Comment 101",
                confidence=0.85,
                evidence_status=EvidenceStatus.VERIFIED,
            )
        ] if consequence_ids is not False else [],
        evidence_comment_ids=["0", "101", "102"],
        confidence=0.9,
        extraction_notes=[],
    )

    return RationaleExtractionResult(
        is_rationale_extracted=is_extracted,
        repository="org/repo",
        entity_number=123,
        resource_type="pull_request",
        source_url="https://github.com/org/repo/pull/123",
        model_name="qwen2.5:7b",
        decisions_evaluated=1,
        rationales=[decision] if is_extracted else [],
        total_evidence_citations=3,
        processing_notes=[],
    )


# ==============================================================================
# Unit tests
# ==============================================================================

@pytest.mark.asyncio
async def test_1_valid_evidence_verified():
    """Verify that a claim with genuine comment citations is marked VERIFIED with DIRECT evidence."""
    thread = make_thread()
    rationale_res = make_rationale_result()

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    assert res.is_verification_completed is True
    assert res.decisions_evaluated == 1
    vdec = res.verified_decisions[0]
    assert vdec.decision_id == "dec-123-1"
    assert vdec.overall_verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED)
    assert len(vdec.claim_verifications) >= 1
    # Check rationale claim
    rat_claim = vdec.claim_verifications[0]
    assert rat_claim.status == VerificationStatus.VERIFIED
    assert rat_claim.evidence_type == EvidenceType.DIRECT
    assert "101" in rat_claim.supporting_comment_ids
    assert len(rat_claim.supporting_provenance) == 1
    assert rat_claim.supporting_provenance[0].author == "bob"


@pytest.mark.asyncio
async def test_2_invalid_comment_ids_unsupported():
    """Verify that a claim citing non-existent comment IDs is marked UNSUPPORTED."""
    thread = make_thread()
    # Rationale cites fake IDs
    rationale_res = make_rationale_result(rationale_ids=["FAKE-999"])

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    vdec = res.verified_decisions[0]
    rat_claim = vdec.claim_verifications[0]
    assert rat_claim.status == VerificationStatus.UNSUPPORTED
    assert rat_claim.evidence_type == EvidenceType.NONE
    assert rat_claim.supporting_comment_ids == []
    assert any("do not exist" in n for n in rat_claim.verification_notes)


@pytest.mark.asyncio
async def test_3_partially_supported_mixed_ids():
    """Verify that a claim citing both valid and invalid comment IDs is PARTIALLY_SUPPORTED."""
    thread = make_thread()
    # Rationale cites valid "101" and invalid "FAKE-999"
    rationale_res = make_rationale_result(rationale_ids=["101", "FAKE-999"])

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    vdec = res.verified_decisions[0]
    rat_claim = vdec.claim_verifications[0]
    assert rat_claim.status == VerificationStatus.PARTIALLY_SUPPORTED
    assert "101" in rat_claim.supporting_comment_ids
    assert "FAKE-999" not in rat_claim.supporting_comment_ids


@pytest.mark.asyncio
async def test_4_contradictory_evidence_detected():
    """Verify that contradictory comments in the thread are detected and flag CONTRADICTED."""
    comments = [
        make_comment("0", "alice", "PR Description: adopt connection pooling"),
        make_comment("101", "bob", "Let's adopt asyncpg pooling"),
        # Contradicting comment with objection signal and claim keywords
        make_comment("103", "david", "I strongly disagree with asyncpg pooling: it breaks connection isolation and introduces a critical regression!"),
    ]
    thread = make_thread(comments=comments)
    # Claim says asyncpg pooling is accepted, but comment 103 strongly disagrees and claims regression
    rationale_res = make_rationale_result(rationale_ids=["101"])

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    vdec = res.verified_decisions[0]
    # At least one claim or decision should note contradiction
    assert vdec.contradicted_count >= 1 or len(vdec.all_contradicting_comment_ids) >= 1
    if vdec.all_contradicting_comment_ids:
        assert "103" in vdec.all_contradicting_comment_ids


@pytest.mark.asyncio
async def test_5_insufficient_evidence_marker_preserved():
    """Verify that explicit insufficient_evidence claim is marked INSUFFICIENT_EVIDENCE."""
    thread = make_thread()
    rationale_res = make_rationale_result()
    # Modify rationale claim to have insufficient_evidence marker
    rationale_res.rationales[0].rationale.statement = "insufficient_evidence: reason not stated"
    rationale_res.rationales[0].rationale.supporting_comment_ids = []

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    rat_claim = res.verified_decisions[0].claim_verifications[0]
    assert rat_claim.status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert rat_claim.confidence == 0.0


@pytest.mark.asyncio
async def test_6_rejected_alternative_distinguishes_mention_from_rejection():
    """Verify that an alternative merely mentioned without rejection signal is not verified as rejected."""
    # Comment 102 only asks about an alternative, without rejecting it
    comments = [
        make_comment("0", "alice", "Propose asyncpg pooling"),
        make_comment("101", "bob", "Adopt asyncpg"),
        make_comment("102", "charlie", "What about psycopg3? Could we use psycopg3?"),
    ]
    thread = make_thread(comments=comments)
    rationale_res = make_rationale_result(
        alternative_ids=["102"],
        alt_statement="psycopg3 alternative",
        alt_rejection="Discarded due to instability",
    )

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    vdec = res.verified_decisions[0]
    alt_claims = [c for c in vdec.claim_verifications if c.claim_type == "rejected_alternative"]
    assert len(alt_claims) == 1
    # Because comment 102 has no rejection keywords ("reject", "won't work", etc.), it shouldn't be fully VERIFIED
    assert alt_claims[0].status in (VerificationStatus.PARTIALLY_SUPPORTED, VerificationStatus.UNSUPPORTED)
    assert any("rejection" in n.lower() for n in alt_claims[0].verification_notes)


@pytest.mark.asyncio
async def test_7_empty_discussion_short_circuits():
    """Verify that an empty discussion thread short-circuits gracefully."""
    thread = make_thread(comments=[], is_empty=True)
    rationale_res = make_rationale_result()

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    assert res.is_verification_completed is False
    assert res.decisions_evaluated == 0
    assert res.verified_decisions == []


@pytest.mark.asyncio
async def test_8_none_or_empty_rationale_result_short_circuits():
    """Verify that None or empty rationale result short-circuits cleanly."""
    thread = make_thread()

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=None)

    assert res.is_verification_completed is False
    assert res.decisions_evaluated == 0


@pytest.mark.asyncio
async def test_9_provenance_metadata_preserved():
    """Verify that provenance (author, created_at, html_url, body_snippet) is accurately attached."""
    thread = make_thread()
    rationale_res = make_rationale_result(rationale_ids=["101"])

    verifier = EvidenceVerifier()
    res = await verifier.verify(thread=thread, rationale_result=rationale_res)

    vdec = res.verified_decisions[0]
    rat_claim = vdec.claim_verifications[0]
    assert len(rat_claim.supporting_provenance) == 1
    prov = rat_claim.supporting_provenance[0]
    assert prov.comment_id == "101"
    assert prov.author == "bob"
    assert prov.html_url == "https://github.com/org/repo/pull/123#issuecomment-101"
    assert "asyncpg" in prov.body_snippet


def test_10_deterministic_rule_tokenize():
    """Unit test for tokenization and stopword removal."""
    tokens = tokenize_statement("We should adopt asyncpg connection pooling for PostgreSQL!")
    assert "asyncpg" in tokens
    assert "connection" in tokens
    assert "pooling" in tokens
    assert "postgresql" in tokens
    assert "should" not in tokens
    assert "for" not in tokens


@pytest.mark.asyncio
async def test_11_functional_entrypoint():
    """Verify verify_evidence functional entrypoint delegates cleanly."""
    thread = make_thread()
    rationale_res = make_rationale_result()

    res = await verify_evidence(thread=thread, rationale_result=rationale_res)
    assert res.is_verification_completed is True
    assert res.decisions_evaluated == 1
