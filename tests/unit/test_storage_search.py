"""Comprehensive unit tests for Module 9: Storage and Search."""

from datetime import datetime, timezone
import os
import sqlite3
import pytest

from app.adr_generation.generator import ADRGenerator
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
from app.search.filters import build_filter_clauses
from app.search.schemas import SearchFilters
from app.search.service import SearchService
from app.storage.database import get_connection, init_db
from app.storage.repository import StorageRepository


@pytest.fixture
def temp_db_path(tmp_path):
    """Provides an isolated SQLite database path for testing."""
    return str(tmp_path / "test_primordial.db")


def make_test_thread(
    repo: str = "nodejs/node",
    entity_number: int = 41749,
    title: str = "Adopt Undici for Fetch API",
) -> CleanedDiscussionThread:
    comments = [
        CleanedDiscussionComment(
            id="1",
            comment_type=CommentType.CONVERSATION,
            author="mcollina",
            author_association="MEMBER",
            body="Undici provides high throughput and streaming support.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url=f"https://github.com/{repo}/pull/{entity_number}#issuecomment-1",
        ),
        CleanedDiscussionComment(
            id="2",
            comment_type=CommentType.CONVERSATION,
            author="ronag",
            author_association="MEMBER",
            body="node-fetch was rejected because of performance regressions under concurrent load.",
            created_at=datetime(2022, 2, 1, 11, 0, 0, tzinfo=timezone.utc),
            html_url=f"https://github.com/{repo}/pull/{entity_number}#issuecomment-2",
        ),
    ]
    owner, name = repo.split("/")
    return CleanedDiscussionThread(
        repository_owner=owner,
        repository_name=name,
        entity_number=entity_number,
        resource_type="pull_request",
        title=title,
        body="Propose native fetch support in Node.js core.",
        state="closed",
        author="mcollina",
        created_at=datetime(2022, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2022, 2, 2, 9, 0, 0, tzinfo=timezone.utc),
        html_url=f"https://github.com/{repo}/pull/{entity_number}",
        comments=comments,
        audit=PreprocessingAudit(
            total_comments_input=2,
            substantive_comments_retained=2,
            comments_removed=0,
            is_empty=False,
        ),
        estimated_tokens=250,
    )


def make_test_verification_result(
    repo: str = "nodejs/node",
    entity_number: int = 41749,
) -> EvidenceVerificationResult:
    claim1 = ClaimVerificationResult(
        claim_id=f"dec-{entity_number}-1-rationale",
        claim_type="rationale",
        claim_text="Undici provides high throughput and streaming support",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.DIRECT,
        supporting_comment_ids=["1"],
        contradicting_comment_ids=[],
        supporting_provenance=[
            CommentProvenance(
                comment_id="1",
                author="mcollina",
                author_association="MEMBER",
                created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
                html_url=f"https://github.com/{repo}/pull/{entity_number}#issuecomment-1",
                body_snippet="Undici provides high throughput",
            )
        ],
        contradicting_provenance=[],
        explanation="Corroborated by comment 1",
        confidence=0.95,
        verification_notes=[],
    )
    claim2 = ClaimVerificationResult(
        claim_id=f"dec-{entity_number}-1-alt-0",
        claim_type="rejected_alternative",
        claim_text="node-fetch userland wrapper",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.DIRECT,
        supporting_comment_ids=["2"],
        contradicting_comment_ids=[],
        supporting_provenance=[
            CommentProvenance(
                comment_id="2",
                author="ronag",
                author_association="MEMBER",
                created_at=datetime(2022, 2, 1, 11, 0, 0, tzinfo=timezone.utc),
                html_url=f"https://github.com/{repo}/pull/{entity_number}#issuecomment-2",
                body_snippet="node-fetch was rejected",
            )
        ],
        contradicting_provenance=[],
        explanation="Rejected due to performance regressions",
        confidence=0.90,
        verification_notes=[],
    )

    vdec = DecisionVerificationResult(
        decision_id=f"dec-{entity_number}-1",
        decision_summary="Adopt Undici for native Fetch implementation in core",
        candidate_status="accepted",
        overall_verification_status=VerificationStatus.VERIFIED,
        claim_verifications=[claim1, claim2],
        all_supporting_comment_ids=["1", "2"],
        all_contradicting_comment_ids=[],
        total_claims_evaluated=2,
        verified_claims_count=2,
        partially_supported_count=0,
        contradicted_count=0,
        unsupported_count=0,
        confidence=0.95,
        verification_notes=[],
    )

    return EvidenceVerificationResult(
        is_verification_completed=True,
        repository=repo,
        entity_number=entity_number,
        resource_type="pull_request",
        source_url=f"https://github.com/{repo}/pull/{entity_number}",
        model_name="qwen2.5:7b",
        decisions_evaluated=1,
        verified_decisions=[vdec],
        total_claims_verified=2,
        total_claims_contradicted=0,
        total_claims_unsupported=0,
        processing_notes=[],
    )


# ==============================================================================
# Unit tests
# ==============================================================================

def test_1_database_initialization(temp_db_path):
    """Verify init_db creates all required tables and indexes."""
    init_db(temp_db_path)
    assert os.path.exists(temp_db_path)

    conn = get_connection(temp_db_path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = {r["name"] for r in cur.fetchall()}
    conn.close()

    expected_tables = {
        "repositories", "discussions", "comments",
        "decisions", "claims", "alternatives",
        "verifications", "adrs"
    }
    assert expected_tables.issubset(table_names)


def test_2_save_and_retrieve_decision(temp_db_path):
    """Verify full save and retrieval of discussion, decision, claims, and ADR."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)

    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)

    res = repo.save_pipeline_result(thread=thread, verification_result=v_res, adr_result=adr_res)
    assert res["saved_decisions_count"] == 1

    dec = repo.get_decision("dec-41749-1")
    assert dec is not None
    assert dec["decision_summary"] == "Adopt Undici for native Fetch implementation in core"
    assert dec["status"] == "accepted"
    assert dec["repository"] == "nodejs/node"
    assert len(dec["claims"]) == 2
    assert len(dec["alternatives"]) == 1
    assert dec["adr"] is not None
    assert dec["adr"]["adr_id"] == "ADR-41749-01"


def test_3_duplicate_prevention_idempotency(temp_db_path):
    """Verify saving the same discussion multiple times updates without duplicating rows."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)

    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)

    # Save twice
    repo.save_pipeline_result(thread, v_res, adr_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    conn = get_connection(temp_db_path)
    count_disc = conn.execute("SELECT COUNT(*) as c FROM discussions").fetchone()["c"]
    count_dec = conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
    count_claims = conn.execute("SELECT COUNT(*) as c FROM claims").fetchone()["c"]
    conn.close()

    assert count_disc == 1
    assert count_dec == 1
    assert count_claims == 2


def test_4_foreign_key_cascade(temp_db_path):
    """Verify foreign key constraint deletes cascading child records."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)

    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    conn = get_connection(temp_db_path)
    conn.execute("DELETE FROM discussions WHERE id = 'nodejs/node#41749'")
    conn.commit()

    dec_count = conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
    claim_count = conn.execute("SELECT COUNT(*) as c FROM claims").fetchone()["c"]
    conn.close()

    assert dec_count == 0
    assert claim_count == 0


def test_5_search_by_keyword(temp_db_path):
    """Verify SearchService finds decisions by technology keyword."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    search_svc = SearchService(temp_db_path)
    result = search_svc.search("Undici")

    assert result.total_hits == 1
    hit = result.hits[0]
    assert hit.decision_id == "dec-41749-1"
    assert "Undici" in hit.summary
    assert hit.repository == "nodejs/node"


def test_6_search_by_rejected_alternative(temp_db_path):
    """Verify search finds decisions matching rejected alternatives."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    search_svc = SearchService(temp_db_path)
    result = search_svc.search("node-fetch")

    assert result.total_hits == 1
    assert result.hits[0].decision_id == "dec-41749-1"


def test_7_search_filters(temp_db_path):
    """Verify SearchFilters restricts matches by repo and status."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    search_svc = SearchService(temp_db_path)

    # Correct filter matches
    f_match = SearchFilters(repository="nodejs/node", status="accepted")
    res_match = search_svc.search("Undici", filters=f_match)
    assert res_match.total_hits == 1

    # Non-matching repo
    f_no_match = SearchFilters(repository="django/django")
    res_no = search_svc.search("Undici", filters=f_no_match)
    assert res_no.total_hits == 0


def test_8_list_decisions(temp_db_path):
    """Verify list_decisions returns summary records."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    decisions = repo.list_decisions()
    assert len(decisions) == 1
    assert decisions[0]["decision_id"] == "dec-41749-1"
    assert decisions[0]["repository"] == "nodejs/node"


def test_9_get_adr(temp_db_path):
    """Verify get_adr retrieves ADR record by ADR ID."""
    init_db(temp_db_path)
    repo = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)

    adr_rec = repo.get_adr("ADR-41749-01")
    assert adr_rec is not None
    assert adr_rec["title"] == "Adopt Undici for native Fetch implementation in core"
    assert "ADR-41749-01" in adr_rec["markdown_content"]


def test_10_persistence_survives_reconnect(temp_db_path):
    """Verify data persists across multiple distinct database connections."""
    init_db(temp_db_path)

    # Session 1: write
    repo1 = StorageRepository(temp_db_path)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo1.save_pipeline_result(thread, v_res, adr_res)

    # Session 2: new repository instance on existing file
    repo2 = StorageRepository(temp_db_path)
    dec = repo2.get_decision("dec-41749-1")
    assert dec is not None
    assert dec["decision_summary"] == "Adopt Undici for native Fetch implementation in core"

