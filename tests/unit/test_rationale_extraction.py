"""Comprehensive unit tests for Module 5: Rationale and Argument Extraction."""

from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import AIModelResponseException, SchemaValidationException
from app.decision_detection.model_client import OllamaModelClient
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
)
from app.domain.entities import CommentType
from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    PreprocessingAudit,
)
from app.rationale_extraction.extractor import RationaleExtractor, extract_decision_rationale
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    RejectedAlternative,
    RawDecisionRationale,
)
from app.rationale_extraction.validators import (
    validate_claim_evidence,
    validate_rejected_alternative,
    validate_decision_rationale,
)


# ==============================================================================
# Test helpers and fixtures
# ==============================================================================

def make_test_comment(
    comment_id: str,
    author: str = "alice",
    body: str = "Technical discussion comment",
    comment_type: CommentType = CommentType.CONVERSATION,
) -> CleanedDiscussionComment:
    """Helper to create a test CleanedDiscussionComment."""
    return CleanedDiscussionComment(
        id=comment_id,
        comment_type=comment_type,
        author=author,
        author_association="MEMBER",
        body=body,
        created_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        html_url=f"https://github.com/org/repo/pull/123#issuecomment-{comment_id}",
    )


def make_test_thread(
    comments: Optional[List[CleanedDiscussionComment]] = None,
    is_empty: bool = False,
    title: str = "Refactor Database Layer to Use Connection Pooling",
) -> CleanedDiscussionThread:
    """Helper to create a test CleanedDiscussionThread."""
    cmt_list = comments if comments is not None else [
        make_test_comment("0", "alice", "PR Description: propose connection pooling", CommentType.DESCRIPTION),
        make_test_comment("101", "bob", "LGTM, let's adopt asyncpg connection pooling"),
        make_test_comment("102", "charlie", "We considered psycopg2 but rejected it due to sync blocking"),
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
        title=title,
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


def make_detection_result(
    decisions: Optional[List[CandidateDecision]] = None,
    is_detected: bool = True,
) -> DecisionDetectionResult:
    """Helper to create a test DecisionDetectionResult."""
    if decisions is None:
        decisions = [
            CandidateDecision(
                decision_id="dec-123-1",
                decision_statement="Adopt asyncpg connection pooling for PostgreSQL access",
                status=CandidateDecisionStatus.ACCEPTED,
                confidence=0.95,
                supporting_comment_ids=["0", "101"],
                repository="org/repo",
                entity_number=123,
                resource_type="pull_request",
                source_title="Refactor Database Layer to Use Connection Pooling",
                model_name="qwen2.5:7b",
            )
        ]
    return DecisionDetectionResult(
        is_decision_detected=is_detected,
        decisions=decisions if is_detected else [],
        total_decisions=len(decisions) if is_detected else 0,
        model_name="qwen2.5:7b",
        repository="org/repo",
        entity_number=123,
        resource_type="pull_request",
        source_url="https://github.com/org/repo/pull/123",
        processing_notes=[],
    )


def make_raw_rationale_response(
    decision_id: str = "dec-123-1",
    rationale_ids: Optional[List[str]] = None,
    supporting_ids: Optional[List[str]] = None,
    opposing_ids: Optional[List[str]] = None,
    alternative_ids: Optional[List[str]] = None,
    tradeoff_ids: Optional[List[str]] = None,
    consequence_ids: Optional[List[str]] = None,
    is_extracted: bool = True,
    alternative_rejection_reason: Optional[str] = "Causes sync I/O blocking",
) -> dict:
    """Build a well-formed mock LLM response dict for rationale extraction."""
    return {
        "is_rationale_extracted": is_extracted,
        "rationales": [
            {
                "decision_id": decision_id,
                "decision_summary": "Adopt asyncpg connection pooling for PostgreSQL access",
                "rationale": {
                    "statement": "asyncpg provides native async support with higher throughput than psycopg2",
                    "supporting_comment_ids": rationale_ids if rationale_ids is not None else ["101"],
                    "evidence_explanation": "Comment 101 directly advocates adopting asyncpg",
                    "confidence": 0.92,
                },
                "supporting_arguments": [
                    {
                        "statement": "Connection pooling reduces database contention under load",
                        "supporting_comment_ids": supporting_ids if supporting_ids is not None else ["0", "101"],
                        "evidence_explanation": "PR description and bob's comment support this",
                        "confidence": 0.88,
                    }
                ] if supporting_ids is not False else [],
                "opposing_arguments": [
                    {
                        "statement": "Some team members raised concerns about asyncpg complexity",
                        "supporting_comment_ids": opposing_ids if opposing_ids else [],
                        "evidence_explanation": "Discussion mentioned concerns",
                        "confidence": 0.70,
                    }
                ] if opposing_ids else [],
                "rejected_alternatives": [
                    {
                        "statement": "psycopg2 synchronous adapter",
                        "rejection_reason": alternative_rejection_reason,
                        "supporting_comment_ids": alternative_ids if alternative_ids is not None else ["102"],
                        "evidence_explanation": "Comment 102 explicitly rejected psycopg2",
                        "confidence": 0.90,
                    }
                ] if alternative_ids is not False else [],
                "trade_offs": [
                    {
                        "statement": "Migrating to asyncpg requires updating all existing query code",
                        "supporting_comment_ids": tradeoff_ids if tradeoff_ids is not None else ["0"],
                        "evidence_explanation": "PR description mentions migration effort",
                        "confidence": 0.80,
                    }
                ] if tradeoff_ids is not False else [],
                "consequences": [
                    {
                        "statement": "Higher throughput under concurrent load",
                        "supporting_comment_ids": consequence_ids if consequence_ids is not None else ["101"],
                        "evidence_explanation": "Comment 101 cites performance benefits",
                        "confidence": 0.85,
                    }
                ] if consequence_ids is not False else [],
                "confidence": 0.91,
                "extraction_notes": None,
            }
        ],
        "deliberation_summary": None,
    }


# ==============================================================================
# 1. Happy path: rationale extracted for accepted decision
# ==============================================================================
@pytest.mark.asyncio
async def test_1_happy_path_rationale_extracted():
    """Verify successful rationale extraction for an accepted decision with valid evidence."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=make_raw_rationale_response())

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is True
    assert result.repository == "org/repo"
    assert result.entity_number == 123
    assert result.resource_type == "pull_request"
    assert result.model_name == "qwen2.5:7b"
    assert result.decisions_evaluated == 1
    assert len(result.rationales) == 1

    rat = result.rationales[0]
    assert rat.decision_id == "dec-123-1"
    assert rat.status == "accepted"
    assert "asyncpg" in rat.rationale.statement
    assert rat.rationale.evidence_status == EvidenceStatus.VERIFIED


# ==============================================================================
# 2. Supporting arguments are extracted and grounded
# ==============================================================================
@pytest.mark.asyncio
async def test_2_supporting_arguments_extracted():
    """Verify supporting arguments are grounded to real comment IDs."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(supporting_ids=["0", "101"])
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert len(rat.supporting_arguments) == 1
    arg = rat.supporting_arguments[0]
    assert arg.evidence_status == EvidenceStatus.VERIFIED
    assert "0" in arg.supporting_comment_ids
    assert "101" in arg.supporting_comment_ids


# ==============================================================================
# 3. Opposing arguments extracted when present
# ==============================================================================
@pytest.mark.asyncio
async def test_3_opposing_arguments_extracted():
    """Verify opposing arguments with valid comment IDs are preserved."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(opposing_ids=["102"])
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert len(rat.opposing_arguments) == 1
    assert "102" in rat.opposing_arguments[0].supporting_comment_ids


# ==============================================================================
# 4. No opposing arguments when model returns empty list
# ==============================================================================
@pytest.mark.asyncio
async def test_4_no_opposing_arguments_empty():
    """Verify result has empty opposing_arguments when model returns [] (silence != disagreement)."""
    thread = make_test_thread()
    detection = make_detection_result()

    response = make_raw_rationale_response()
    response["rationales"][0]["opposing_arguments"] = []

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=response)

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.rationales[0].opposing_arguments == []


# ==============================================================================
# 5. Rejected alternatives extracted with stated reason
# ==============================================================================
@pytest.mark.asyncio
async def test_5_rejected_alternatives_extracted():
    """Verify rejected alternatives are extracted with stated rejection reason."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(
            alternative_ids=["102"],
            alternative_rejection_reason="Causes sync I/O blocking under async event loop",
        )
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert len(rat.rejected_alternatives) == 1
    alt = rat.rejected_alternatives[0]
    assert "psycopg2" in alt.statement
    assert "Causes sync I/O blocking" in alt.rejection_reason
    assert "102" in alt.supporting_comment_ids


# ==============================================================================
# 6. Rejected alternative without reason defaults to placeholder
# ==============================================================================
@pytest.mark.asyncio
async def test_6_rejected_alternative_missing_reason_defaults():
    """Verify rejected alternative with null rejection_reason gets placeholder text."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(
            alternative_ids=["102"],
            alternative_rejection_reason="unknown",
        )
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    alt = result.rationales[0].rejected_alternatives[0]
    assert alt.rejection_reason == "Unspecified in public thread"


# ==============================================================================
# 7. Trade-offs extracted and verified
# ==============================================================================
@pytest.mark.asyncio
async def test_7_trade_offs_extracted():
    """Verify trade-offs are extracted and evidence grounded."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(tradeoff_ids=["0"])
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert len(rat.trade_offs) == 1
    assert "0" in rat.trade_offs[0].supporting_comment_ids


# ==============================================================================
# 8. Consequences extracted and verified
# ==============================================================================
@pytest.mark.asyncio
async def test_8_consequences_extracted():
    """Verify consequences are extracted and evidence grounded."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(consequence_ids=["101"])
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert len(rat.consequences) == 1
    assert "101" in rat.consequences[0].supporting_comment_ids


# ==============================================================================
# 9. Hallucinated comment IDs are stripped
# ==============================================================================
@pytest.mark.asyncio
async def test_9_hallucinated_ids_stripped_ungrounded_claim_dropped():
    """Verify hallucinated comment IDs are stripped and resulting ungrounded claims dropped."""
    thread = make_test_thread()
    detection = make_detection_result()

    # The model cites non-existent comment IDs for the supporting argument
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(supporting_ids=["FAKE-999", "HALLUCINATED-42"])
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    # Supporting argument was entirely hallucinated → dropped
    rat = result.rationales[0]
    assert rat.supporting_arguments == []


# ==============================================================================
# 10. Insufficient evidence marker preserves claim with INSUFFICIENT_EVIDENCE status
# ==============================================================================
@pytest.mark.asyncio
async def test_10_insufficient_evidence_marker_preserved():
    """Verify explicit 'insufficient_evidence' marker preserves claim with correct status."""
    thread = make_test_thread()
    detection = make_detection_result()

    response = make_raw_rationale_response()
    # Modify rationale to explicitly signal insufficient evidence (no valid IDs)
    response["rationales"][0]["rationale"] = {
        "statement": "insufficient_evidence: rationale not stated in discussion",
        "supporting_comment_ids": [],  # no IDs
        "evidence_explanation": "Rationale not found",
        "confidence": 0.1,
    }

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=response)

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert rat.rationale.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert rat.rationale.confidence == 0.0


# ==============================================================================
# 11. Empty discussion short-circuits without model call
# ==============================================================================
@pytest.mark.asyncio
async def test_11_empty_discussion_short_circuits():
    """Verify empty discussion short-circuits before any model call."""
    thread = make_test_thread(comments=[], is_empty=True)
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock()

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is False
    assert result.decisions_evaluated == 0
    mock_client.generate_chat.assert_not_called()


# ==============================================================================
# 12. No detected decisions short-circuits without model call
# ==============================================================================
@pytest.mark.asyncio
async def test_12_no_detected_decisions_short_circuits():
    """Verify no-decisions state short-circuits before any model call."""
    thread = make_test_thread()
    detection = make_detection_result(decisions=[], is_detected=False)

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock()

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is False
    assert result.decisions_evaluated == 0
    mock_client.generate_chat.assert_not_called()


# ==============================================================================
# 13. Missing is_rationale_extracted triggers retry, succeeds on attempt 2
# ==============================================================================
@pytest.mark.asyncio
async def test_13_missing_is_rationale_extracted_triggers_retry():
    """Verify missing required field triggers one correction retry that succeeds."""
    thread = make_test_thread()
    detection = make_detection_result()

    invalid_response = make_raw_rationale_response()
    del invalid_response["is_rationale_extracted"]  # required field removed

    valid_response = make_raw_rationale_response()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(side_effect=[invalid_response, valid_response])

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b", max_retries=1)
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is True
    assert mock_client.generate_chat.call_count == 2
    assert any("correction retry" in note for note in result.processing_notes)


# ==============================================================================
# 14. Missing rationales field triggers retry, succeeds on attempt 2
# ==============================================================================
@pytest.mark.asyncio
async def test_14_missing_rationales_triggers_retry():
    """Verify missing required 'rationales' field triggers retry and recovers."""
    thread = make_test_thread()
    detection = make_detection_result()

    invalid_response = make_raw_rationale_response()
    del invalid_response["rationales"]  # required field removed

    valid_response = make_raw_rationale_response()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(side_effect=[invalid_response, valid_response])

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b", max_retries=1)
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is True
    assert mock_client.generate_chat.call_count == 2


# ==============================================================================
# 15. Malformed JSON / AIModelResponseException triggers retry and recovers
# ==============================================================================
@pytest.mark.asyncio
async def test_15_malformed_json_triggers_retry_and_recovers():
    """Verify AIModelResponseException triggers retry; second attempt succeeds."""
    thread = make_test_thread()
    detection = make_detection_result()

    valid_response = make_raw_rationale_response()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        side_effect=[
            AIModelResponseException(
                message="Invalid JSON from model",
                details={"raw_content": "{ invalid json }"},
            ),
            valid_response,
        ]
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b", max_retries=1)
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.is_rationale_extracted is True
    assert mock_client.generate_chat.call_count == 2


# ==============================================================================
# 16. Retry exhaustion on persistent schema failure raises SchemaValidationException
# ==============================================================================
@pytest.mark.asyncio
async def test_16_retry_exhaustion_schema_raises():
    """Verify persistent schema validation failure raises SchemaValidationException with retry_exhausted."""
    thread = make_test_thread()
    detection = make_detection_result()

    # Both attempts return response missing the required field
    invalid_response = {"is_rationale_extracted": True}  # 'rationales' key missing

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=invalid_response)

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b", max_retries=1)

    with pytest.raises(SchemaValidationException) as exc_info:
        await extractor.extract(thread=thread, detection_result=detection)

    assert mock_client.generate_chat.call_count == 2
    assert exc_info.value.details.get("retry_exhausted") is True


# ==============================================================================
# 17. Retry exhaustion on persistent JSON failure re-raises AIModelResponseException
# ==============================================================================
@pytest.mark.asyncio
async def test_17_retry_exhaustion_json_raises():
    """Verify persistent AIModelResponseException is re-raised after exhausting retries."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        side_effect=AIModelResponseException(
            message="Repeated JSON parse failure",
            details={"raw_content": ""},
        )
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b", max_retries=1)

    with pytest.raises(AIModelResponseException) as exc_info:
        await extractor.extract(thread=thread, detection_result=detection)

    assert mock_client.generate_chat.call_count == 2
    assert "JSON" in exc_info.value.message


# ==============================================================================
# 18. Multiple decisions: rationale extracted for each
# ==============================================================================
@pytest.mark.asyncio
async def test_18_multiple_decisions_extracted():
    """Verify rationale is extracted for each of multiple detected decisions."""
    thread = make_test_thread()
    decisions = [
        CandidateDecision(
            decision_id="dec-123-1",
            decision_statement="Adopt asyncpg",
            status=CandidateDecisionStatus.ACCEPTED,
            confidence=0.90,
            supporting_comment_ids=["101"],
            repository="org/repo",
            entity_number=123,
            resource_type="pull_request",
            source_title="Refactor DB",
            model_name="qwen2.5:7b",
        ),
        CandidateDecision(
            decision_id="dec-123-2",
            decision_statement="Use connection pool of size 10",
            status=CandidateDecisionStatus.ACCEPTED,
            confidence=0.80,
            supporting_comment_ids=["102"],
            repository="org/repo",
            entity_number=123,
            resource_type="pull_request",
            source_title="Refactor DB",
            model_name="qwen2.5:7b",
        ),
    ]
    detection = make_detection_result(decisions=decisions)

    multi_response = {
        "is_rationale_extracted": True,
        "rationales": [
            {
                "decision_id": "dec-123-1",
                "decision_summary": "Adopt asyncpg",
                "rationale": {
                    "statement": "asyncpg is async-native",
                    "supporting_comment_ids": ["101"],
                    "evidence_explanation": "Comment 101 supports this",
                    "confidence": 0.90,
                },
                "supporting_arguments": [],
                "opposing_arguments": [],
                "rejected_alternatives": [],
                "trade_offs": [],
                "consequences": [],
                "confidence": 0.90,
                "extraction_notes": None,
            },
            {
                "decision_id": "dec-123-2",
                "decision_summary": "Use connection pool size 10",
                "rationale": {
                    "statement": "Pool size 10 balances resource use",
                    "supporting_comment_ids": ["102"],
                    "evidence_explanation": "Comment 102 discusses pool sizing",
                    "confidence": 0.80,
                },
                "supporting_arguments": [],
                "opposing_arguments": [],
                "rejected_alternatives": [],
                "trade_offs": [],
                "consequences": [],
                "confidence": 0.80,
                "extraction_notes": None,
            },
        ],
        "deliberation_summary": None,
    }

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=multi_response)

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    assert result.decisions_evaluated == 2
    assert len(result.rationales) == 2
    assert result.rationales[0].decision_id == "dec-123-1"
    assert result.rationales[1].decision_id == "dec-123-2"


# ==============================================================================
# 19. All evidence hallucinated for rationale: marked INSUFFICIENT_EVIDENCE, not dropped
# ==============================================================================
@pytest.mark.asyncio
async def test_19_all_evidence_hallucinated_marks_insufficient():
    """Verify a rationale with entirely hallucinated IDs gets INSUFFICIENT_EVIDENCE, not dropped."""
    thread = make_test_thread()
    detection = make_detection_result()

    response = make_raw_rationale_response()
    # Rationale cites only hallucinated IDs
    response["rationales"][0]["rationale"]["supporting_comment_ids"] = ["FAKE-1", "FAKE-2"]

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=response)

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    rat = result.rationales[0]
    assert rat.rationale.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    # Decision record must still exist
    assert rat.decision_id == "dec-123-1"


# ==============================================================================
# 20. Metadata preservation in result
# ==============================================================================
@pytest.mark.asyncio
async def test_20_metadata_preservation():
    """Verify result metadata fields match thread and model name."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=make_raw_rationale_response())

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection, model_name="qwen2.5:7b")

    assert result.repository == "org/repo"
    assert result.entity_number == 123
    assert result.resource_type == "pull_request"
    assert result.source_url == "https://github.com/org/repo/pull/123"
    assert result.model_name == "qwen2.5:7b"


# ==============================================================================
# 21. Token budget truncation noted in processing_notes
# ==============================================================================
@pytest.mark.asyncio
async def test_21_token_budget_truncation_noted():
    """Verify that token budget truncation adds a processing note."""
    # Create a thread with many comments to force truncation at very low ceiling
    comments = [
        make_test_comment(str(i), body="A" * 500)
        for i in range(50)
    ]
    thread = make_test_thread(comments=comments)
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=make_raw_rationale_response())

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    # Use a tiny token ceiling to force truncation
    result = await extractor.extract(thread=thread, detection_result=detection, token_ceiling=100)

    # Should have a truncation note
    truncation_notes = [n for n in result.processing_notes if "truncated" in n.lower()]
    assert len(truncation_notes) >= 1


# ==============================================================================
# 22. Validator: validate_claim_evidence directly
# ==============================================================================
def test_22_validate_claim_evidence_strips_invalid_ids():
    """Unit test: validate_claim_evidence strips invalid IDs and preserves valid ones."""
    claim = ExtractedClaim(
        statement="We adopted asyncpg for pooling",
        supporting_comment_ids=["101", "FAKE-999"],
        evidence_explanation="Comment 101 and fake",
        confidence=0.85,
    )
    valid_ids = {"101", "102", "0"}

    result_claim, notes = validate_claim_evidence(claim, valid_ids)

    assert result_claim is not None
    assert "101" in result_claim.supporting_comment_ids
    assert "FAKE-999" not in result_claim.supporting_comment_ids
    assert any("FAKE-999" in n for n in notes)


def test_22b_validate_claim_evidence_drops_ungrounded_normal_claim():
    """Unit test: validate_claim_evidence drops normal claim with no valid citations."""
    claim = ExtractedClaim(
        statement="Completely unrelated claim",
        supporting_comment_ids=["FAKE-1"],
        evidence_explanation="No real evidence",
        confidence=0.9,
    )
    valid_ids = {"101", "102"}

    result_claim, notes = validate_claim_evidence(claim, valid_ids)

    assert result_claim is None
    assert any("Dropped" in n for n in notes)


def test_22c_validate_claim_evidence_preserves_insufficient_evidence_marker():
    """Unit test: explicit insufficient_evidence marker is preserved with correct status."""
    claim = ExtractedClaim(
        statement="insufficient_evidence: rationale was not specified",
        supporting_comment_ids=[],
        evidence_explanation="Not found",
        confidence=0.8,
    )
    valid_ids = {"101"}

    result_claim, notes = validate_claim_evidence(claim, valid_ids)

    assert result_claim is not None
    assert result_claim.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert result_claim.confidence == 0.0


# ==============================================================================
# 23. Validator: validate_rejected_alternative directly
# ==============================================================================
def test_23_validate_rejected_alternative_valid():
    """Unit test: validate_rejected_alternative preserves alternatives with valid IDs."""
    alt = RejectedAlternative(
        statement="psycopg2 synchronous adapter",
        rejection_reason="Causes blocking under async event loop",
        supporting_comment_ids=["102"],
        evidence_explanation="Comment 102 discusses rejection",
        confidence=0.88,
    )
    valid_ids = {"102", "101"}

    result_alt, notes = validate_rejected_alternative(alt, valid_ids)

    assert result_alt is not None
    assert "102" in result_alt.supporting_comment_ids
    assert result_alt.evidence_status == EvidenceStatus.VERIFIED
    assert result_alt.rejection_reason == "Causes blocking under async event loop"


def test_23b_validate_rejected_alternative_null_reason_defaults():
    """Unit test: null rejection_reason defaults to placeholder."""
    alt = RejectedAlternative(
        statement="psycopg2 synchronous adapter",
        rejection_reason="none",
        supporting_comment_ids=["102"],
        evidence_explanation="Comment 102",
        confidence=0.70,
    )
    valid_ids = {"102"}

    result_alt, notes = validate_rejected_alternative(alt, valid_ids)

    assert result_alt is not None
    assert result_alt.rejection_reason == "Unspecified in public thread"


def test_23c_validate_rejected_alternative_drops_hallucinated():
    """Unit test: alternative with only invalid IDs is dropped."""
    alt = RejectedAlternative(
        statement="Made-up alternative",
        rejection_reason="Not found",
        supporting_comment_ids=["FAKE-1"],
        evidence_explanation="No real evidence",
        confidence=0.6,
    )
    valid_ids = {"101", "102"}

    result_alt, notes = validate_rejected_alternative(alt, valid_ids)

    assert result_alt is None
    assert any("Dropped" in n for n in notes)


# ==============================================================================
# 24. to_dict() serialization: EvidenceStatus serialized as strings
# ==============================================================================
@pytest.mark.asyncio
async def test_24_to_dict_serialization():
    """Verify to_dict() produces JSON-serializable dict with EvidenceStatus as strings."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=make_raw_rationale_response())

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    data = result.to_dict()

    assert isinstance(data["is_rationale_extracted"], bool)
    assert isinstance(data["rationales"], list)

    if data["rationales"]:
        rat_dict = data["rationales"][0]
        assert isinstance(rat_dict["rationale"], dict)
        # evidence_status should be a plain string, not an enum
        assert isinstance(rat_dict["rationale"]["evidence_status"], str)
        assert rat_dict["rationale"]["evidence_status"] in ("verified", "insufficient_evidence", "unsupported")


# ==============================================================================
# 25. extract_decision_rationale functional entrypoint works
# ==============================================================================
@pytest.mark.asyncio
async def test_25_functional_entrypoint():
    """Verify extract_decision_rationale functional entrypoint delegates correctly."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(return_value=make_raw_rationale_response())

    result = await extract_decision_rationale(
        thread=thread,
        detection_result=detection,
        model_name="qwen2.5:7b",
        model_client=mock_client,
    )

    assert result.is_rationale_extracted is True
    assert result.decisions_evaluated == 1


# ==============================================================================
# 26. No decisions detected when detection_result is None
# ==============================================================================
@pytest.mark.asyncio
async def test_26_none_detection_result_short_circuits():
    """Verify None detection_result short-circuits without model call."""
    thread = make_test_thread()

    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock()

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=None)

    assert result.is_rationale_extracted is False
    mock_client.generate_chat.assert_not_called()


# ==============================================================================
# 27. Total evidence citations aggregate is computed correctly
# ==============================================================================
@pytest.mark.asyncio
async def test_27_total_evidence_citations_aggregate():
    """Verify total_evidence_citations counts unique comment IDs across all rationale records."""
    thread = make_test_thread()
    detection = make_detection_result()

    mock_client = MagicMock(spec=OllamaModelClient)
    # Rationale uses "101", supporting uses "0"+"101", tradeoff uses "0", consequence uses "101"
    # alternative_ids=False disables the rejected alternative (which would add "102")
    mock_client.generate_chat = AsyncMock(
        return_value=make_raw_rationale_response(
            rationale_ids=["101"],
            supporting_ids=["0", "101"],
            alternative_ids=False,  # disable rejected alternative to control unique IDs
            tradeoff_ids=["0"],
            consequence_ids=["101"],
        )
    )

    extractor = RationaleExtractor(model_client=mock_client, default_model="qwen2.5:7b")
    result = await extractor.extract(thread=thread, detection_result=detection)

    # Unique IDs across all claims: {"0", "101"}
    assert result.total_evidence_citations == 2
