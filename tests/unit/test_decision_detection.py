"""Comprehensive unit tests for Module 4: AI Decision Detection."""

from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from app.core.exceptions import (
    AIModelResponseException,
    AIModelTimeoutException,
    AIServiceUnavailableException,
    SchemaValidationException,
)
from app.decision_detection.detector import DecisionDetector, detect_decisions
from app.decision_detection.model_client import OllamaModelClient
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
    RawModelDecision,
    RawModelDecisionDetectionResponse,
)
from app.domain.entities import CommentType
from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    PreprocessingAudit,
)


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


# ==============================================================================
# 1. Explicit accepted decision detection
# ==============================================================================
@pytest.mark.asyncio
async def test_1_explicit_accepted_decision():
    """Verify detection of an accepted technical decision with evidence."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Team agreed to adopt asyncpg pooling.",
            "decisions": [
                {
                    "decision_statement": "Adopt asyncpg connection pooling for PostgreSQL access",
                    "status": "accepted",
                    "confidence": 0.95,
                    "supporting_comment_ids": ["0", "101"],
                    "rationale_summary": "High throughput and native async support",
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client, default_model="qwen2.5:7b")
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.total_decisions == 1
    assert len(result.decisions) == 1
    dec = result.decisions[0]
    assert dec.status == CandidateDecisionStatus.ACCEPTED
    assert dec.confidence == 0.95
    assert dec.decision_statement == "Adopt asyncpg connection pooling for PostgreSQL access"
    assert dec.supporting_comment_ids == ["0", "101"]
    assert dec.repository == "org/repo"
    assert dec.entity_number == 123
    assert dec.resource_type == "pull_request"
    assert dec.model_name == "qwen2.5:7b"


# ==============================================================================
# 2. Explicit rejected approach detection
# ==============================================================================
@pytest.mark.asyncio
async def test_2_explicit_rejected_approach():
    """Verify detection of an explicitly declined/rejected approach."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Alternative psycopg2 rejected.",
            "decisions": [
                {
                    "decision_statement": "Reject psycopg2 in favor of async drivers",
                    "status": "rejected",
                    "confidence": 0.90,
                    "supporting_comment_ids": ["102"],
                    "rationale_summary": "Synchronous blocking IO degrades event loop performance",
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert len(result.decisions) == 1
    dec = result.decisions[0]
    assert dec.status == CandidateDecisionStatus.REJECTED
    assert dec.supporting_comment_ids == ["102"]


# ==============================================================================
# 3. Proposed but unconfirmed decision
# ==============================================================================
@pytest.mark.asyncio
async def test_3_proposed_decision():
    """Verify detection of a proposed but unconfirmed design."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Architecture RFC proposed but no consensus reached yet.",
            "decisions": [
                {
                    "decision_statement": "Propose gRPC for inter-service communication",
                    "status": "proposed",
                    "confidence": 0.75,
                    "supporting_comment_ids": ["0"],
                    "rationale_summary": "Under discussion for upcoming microservices",
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.decisions[0].status == CandidateDecisionStatus.PROPOSED


# ==============================================================================
# 4. Deferred decision
# ==============================================================================
@pytest.mark.asyncio
async def test_4_deferred_decision():
    """Verify detection of a decision explicitly postponed to future release."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Team agreed to postpone Redis cache invalidation strategy to v2.",
            "decisions": [
                {
                    "decision_statement": "Defer Redis cache invalidation protocol to v2 milestone",
                    "status": "deferred",
                    "confidence": 0.88,
                    "supporting_comment_ids": ["101"],
                    "rationale_summary": "Avoid scope creep in current release",
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.decisions[0].status == CandidateDecisionStatus.DEFERRED


# ==============================================================================
# 5. Ambiguous discussion (unclear)
# ==============================================================================
@pytest.mark.asyncio
async def test_5_unclear_decision():
    """Verify classification of ambiguous discussion without clear verdict."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Deliberation ended abruptly without agreement on format.",
            "decisions": [
                {
                    "decision_statement": "Choice between YAML vs JSON schema configuration",
                    "status": "unclear",
                    "confidence": 0.60,
                    "supporting_comment_ids": ["101", "102"],
                    "rationale_summary": "Conflicting viewpoints, no final decision recorded",
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.decisions[0].status == CandidateDecisionStatus.UNCLEAR


# ==============================================================================
# 6. Discussion containing no decisions
# ==============================================================================
@pytest.mark.asyncio
async def test_6_no_decision_detected():
    """Verify discussion with bug fix or non-decision discussion returns is_decision_detected=False."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": False,
            "reasoning": "This discussion is a simple typo fix with no architectural deliberation.",
            "decisions": [],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is False
    assert result.total_decisions == 0
    assert result.decisions == []
    assert any("Model Deliberation Reasoning" in n for n in result.processing_notes)


# ==============================================================================
# 7. Multiple decisions in one discussion
# ==============================================================================
@pytest.mark.asyncio
async def test_7_multiple_decisions_in_one_thread():
    """Verify multiple distinct decisions are detected and given unique IDs."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Two decisions reached in thread.",
            "decisions": [
                {
                    "decision_statement": "Adopt asyncpg connection pooling",
                    "status": "accepted",
                    "confidence": 0.95,
                    "supporting_comment_ids": ["0", "101"],
                },
                {
                    "decision_statement": "Decline psycopg2 synchronous driver",
                    "status": "rejected",
                    "confidence": 0.92,
                    "supporting_comment_ids": ["102"],
                },
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.total_decisions == 2
    assert result.decisions[0].decision_id == "dec-123-1"
    assert result.decisions[1].decision_id == "dec-123-2"
    assert result.decisions[0].status == CandidateDecisionStatus.ACCEPTED
    assert result.decisions[1].status == CandidateDecisionStatus.REJECTED


# ==============================================================================
# 8. Conflicting comments handled properly
# ==============================================================================
@pytest.mark.asyncio
async def test_8_conflicting_comments():
    """Verify that conflicting comments are appropriately weighed by the model."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Maintainer overruled contributor objection.",
            "decisions": [
                {
                    "decision_statement": "Adopt strict TLS 1.3 requirement despite objection",
                    "status": "accepted",
                    "confidence": 0.85,
                    "supporting_comment_ids": ["101"],
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is True
    assert result.decisions[0].status == CandidateDecisionStatus.ACCEPTED


# ==============================================================================
# 9. Evidence comment ID validation (hallucinated IDs filtered/rejected)
# ==============================================================================
@pytest.mark.asyncio
async def test_9_evidence_comment_id_validation():
    """Verify that hallucinated comment IDs are stripped, and ungrounded candidates are dropped."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "reasoning": "Testing hallucination filtering.",
            "decisions": [
                {
                    # Cites valid ID '101' AND hallucinated ID '99999'
                    "decision_statement": "Partially grounded decision",
                    "status": "accepted",
                    "confidence": 0.80,
                    "supporting_comment_ids": ["101", "99999"],
                },
                {
                    # Cites ONLY hallucinated ID '88888'
                    "decision_statement": "Completely hallucinated decision",
                    "status": "proposed",
                    "confidence": 0.70,
                    "supporting_comment_ids": ["88888"],
                },
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    # First decision retained with '99999' stripped
    assert result.total_decisions == 1
    assert len(result.decisions) == 1
    assert result.decisions[0].decision_statement == "Partially grounded decision"
    assert result.decisions[0].supporting_comment_ids == ["101"]

    # Notes reflect the filtering and dropping actions
    assert any("Filtered 1 hallucinated comment ID(s)" in n for n in result.processing_notes)
    assert any("Dropped candidate decision" in n for n in result.processing_notes)


@pytest.mark.asyncio
async def test_9b_all_candidates_hallucinated_sets_detected_to_false():
    """If all candidate decisions have only hallucinated IDs, is_decision_detected becomes False."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "decisions": [
                {
                    "decision_statement": "Fake decision",
                    "status": "accepted",
                    "confidence": 0.90,
                    "supporting_comment_ids": ["fake-id-1", "fake-id-2"],
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    result = await detector.detect(thread)

    assert result.is_decision_detected is False
    assert result.total_decisions == 0
    assert result.decisions == []


# ==============================================================================
# 10. Invalid model JSON handling
# ==============================================================================
@pytest.mark.asyncio
async def test_10_invalid_model_json_handling():
    """Verify that malformed or non-JSON model output raises AIModelResponseException."""
    client = OllamaModelClient(base_url="http://localhost:11434")

    # Directly test JSON extraction helper with unparseable text
    with pytest.raises(AIModelResponseException) as exc_info:
        client._extract_json("This is raw text without any JSON structure at all.")

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "AI_MODEL_RESPONSE_ERROR"


# ==============================================================================
# 11. Model timeout handling (AIModelTimeoutException)
# ==============================================================================
@pytest.mark.asyncio
async def test_11_model_timeout_handling():
    """Verify timeout communicating with Ollama raises AIModelTimeoutException."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.post.side_effect = httpx.ReadTimeout("Read timed out")

    client = OllamaModelClient(http_client=mock_http_client, timeout_seconds=1.0)
    with pytest.raises(AIModelTimeoutException) as exc_info:
        await client.generate_chat(prompt="Test prompt")

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "AI_MODEL_TIMEOUT"


# ==============================================================================
# 12. Ollama unavailable handling (AIServiceUnavailableException)
# ==============================================================================
@pytest.mark.asyncio
async def test_12_ollama_unavailable_handling():
    """Verify connection error raises AIServiceUnavailableException."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

    client = OllamaModelClient(http_client=mock_http_client)
    with pytest.raises(AIServiceUnavailableException) as exc_info:
        await client.generate_chat(prompt="Test prompt")

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "AI_SERVICE_UNAVAILABLE"


# ==============================================================================
# 13. Empty cleaned discussion handling
# ==============================================================================
@pytest.mark.asyncio
async def test_13_empty_discussion_handling():
    """Verify empty discussion short-circuits without invoking AI model."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock()

    empty_thread = make_test_thread(comments=[], is_empty=True)
    result = await detect_decisions(empty_thread, model_client=mock_client)

    assert result.is_decision_detected is False
    assert result.total_decisions == 0
    assert result.decisions == []
    assert any("empty" in note.lower() for note in result.processing_notes)
    mock_client.generate_chat.assert_not_called()


# ==============================================================================
# 14. Token-budget truncation handling
# ==============================================================================
@pytest.mark.asyncio
async def test_14_token_budget_truncation_handling():
    """Verify token budget truncation is audited in processing notes."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "decisions": [
                {
                    "decision_statement": "Decision under tight token limit",
                    "status": "accepted",
                    "confidence": 0.90,
                    "supporting_comment_ids": ["0"],
                }
            ],
        }
    )

    thread = make_test_thread()
    detector = DecisionDetector(model_client=mock_client)
    # Set a very low token ceiling to force truncation
    result = await detector.detect(thread, token_ceiling=30)

    assert result.is_decision_detected is True
    assert any("truncated to fit model budget" in note for note in result.processing_notes)


# ==============================================================================
# 15. Preservation of repository and issue/PR metadata
# ==============================================================================
@pytest.mark.asyncio
async def test_15_metadata_preservation():
    """Verify all domain metadata fields are preserved in detection results."""
    mock_client = MagicMock(spec=OllamaModelClient)
    mock_client.generate_chat = AsyncMock(
        return_value={
            "is_decision_detected": True,
            "decisions": [
                {
                    "decision_statement": "Preserve metadata test",
                    "status": "accepted",
                    "confidence": 0.99,
                    "supporting_comment_ids": ["0"],
                }
            ],
        }
    )

    thread = make_test_thread(title="Unique Test Title")
    result = await detect_decisions(thread, model_client=mock_client, model_name="qwen2.5:7b")

    # Check top-level result
    assert result.repository == "org/repo"
    assert result.entity_number == 123
    assert result.resource_type == "pull_request"
    assert result.source_url == "https://github.com/org/repo/pull/123"
    assert result.model_name == "qwen2.5:7b"

    # Check candidate decision fields
    dec = result.decisions[0]
    assert dec.repository == "org/repo"
    assert dec.entity_number == 123
    assert dec.resource_type == "pull_request"
    assert dec.source_title == "Unique Test Title"
    assert dec.model_name == "qwen2.5:7b"
    assert dec.decision_id == "dec-123-1"


# ==============================================================================
# Model Client JSON parsing variations
# ==============================================================================
def test_model_client_extract_json_variations():
    """Verify OllamaModelClient._extract_json handles clean JSON, code fences, and embedded JSON."""
    # 1. Clean JSON
    res1 = OllamaModelClient._extract_json('{"key": "value"}')
    assert res1 == {"key": "value"}

    # 2. Markdown fenced JSON
    res2 = OllamaModelClient._extract_json('```json\n{"key": "fenced"}\n```')
    assert res2 == {"key": "fenced"}

    # 3. Embedded JSON with preamble
    res3 = OllamaModelClient._extract_json('Here is the output:\n{"key": "embedded"}\nHope this helps!')
    assert res3 == {"key": "embedded"}


# ==============================================================================
# Status normalization in RawModelDecision
# ==============================================================================
def test_status_normalization_and_confidence_clamping():
    """Verify status normalization handles synonyms and confidence clamping."""
    # Approved -> accepted
    d1 = RawModelDecision(
        decision_statement="Test",
        status="approved",
        confidence=1.5,
        supporting_comment_ids=["0"],
    )
    assert d1.status == CandidateDecisionStatus.ACCEPTED
    assert d1.confidence == 1.0  # Clamped to 1.0

    # Declined -> rejected
    d2 = RawModelDecision(
        decision_statement="Test",
        status="declined",
        confidence=-0.5,
        supporting_comment_ids=["0"],
    )
    assert d2.status == CandidateDecisionStatus.REJECTED
    assert d2.confidence == 0.0  # Clamped to 0.0

    # Postponed -> deferred
    d3 = RawModelDecision(
        decision_statement="Test",
        status="postponed",
        confidence=0.8,
        supporting_comment_ids=["0"],
    )
    assert d3.status == CandidateDecisionStatus.DEFERRED
