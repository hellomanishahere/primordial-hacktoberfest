"""Comprehensive unit tests for Module 10: Historical PR Radar."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.exceptions import InvalidGitHubURLException
from app.pr_radar.analyzer import PullRequestAnalyzer
from app.pr_radar.matcher import HistoricalDecisionMatcher
from app.pr_radar.reporter import generate_radar_report
from app.pr_radar.schemas import (
    ChangedFile,
    HistoricalMatch,
    MatchCategory,
    PullRequestAnalysis,
)
from app.storage.database import init_db
from app.storage.repository import StorageRepository
from tests.unit.test_storage_search import (
    make_test_thread,
    make_test_verification_result,
)
from app.adr_generation.generator import ADRGenerator


@pytest.fixture
def seeded_db(tmp_path):
    """Initializes and seeds a test database with an accepted decision and rejected alternative."""
    db_file = str(tmp_path / "radar_test.db")
    init_db(db_file)
    repo = StorageRepository(db_file)
    thread = make_test_thread(repo="nodejs/node", entity_number=41749)
    v_res = make_test_verification_result(repo="nodejs/node", entity_number=41749)
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)
    return db_file


# ==============================================================================
# Unit tests
# ==============================================================================

def test_1_previously_rejected_approach_detected(seeded_db):
    """Verify that a PR reintroducing a rejected alternative is flagged as PREVIOUSLY_REJECTED_APPROACH."""
    # A new PR proposing node-fetch userland wrapper
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50001,
        title="Re-add node-fetch userland wrapper for fetch compatibility",
        url="https://github.com/nodejs/node/pull/50001",
        author="newbie",
        description="We should re-evaluate node-fetch as an alternative wrapper.",
        changed_files=[
            ChangedFile(filename="lib/internal/bootstrap/fetch.js", status="modified", additions=50, deletions=10)
        ],
    )

    matcher = HistoricalDecisionMatcher(seeded_db)
    matches = matcher.match(pr, threshold=0.4)

    assert len(matches) >= 1
    rejection_matches = [m for m in matches if m.category == MatchCategory.PREVIOUSLY_REJECTED_APPROACH]
    assert len(rejection_matches) == 1
    assert "node-fetch" in rejection_matches[0].relevance_explanation
    assert rejection_matches[0].decision_id == "dec-41749-1"


def test_2_potential_conflict_detected(seeded_db):
    """Verify that a PR modifying an adopted decision's scope with conflicting intent is flagged as POTENTIAL_CONFLICT."""
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50002,
        title="Revert and replace Undici implementation in fetch core",
        url="https://github.com/nodejs/node/pull/50002",
        author="dev",
        description="Propose to remove and replace Undici native fetch with custom socket logic.",
        changed_files=[
            ChangedFile(filename="deps/undici/undici.js", status="removed", additions=0, deletions=5000)
        ],
    )

    matcher = HistoricalDecisionMatcher(seeded_db)
    matches = matcher.match(pr, threshold=0.4)

    assert len(matches) >= 1
    conflict_matches = [m for m in matches if m.category == MatchCategory.POTENTIAL_CONFLICT]
    assert len(conflict_matches) >= 1
    assert "conflict" in conflict_matches[0].relevance_explanation.lower()


def test_3_related_decision_matching(seeded_db):
    """Verify that a PR touching related concepts is flagged as RELATED_DECISION."""
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50003,
        title="Optimize Undici HTTP pipeline throughput in fetch core",
        url="https://github.com/nodejs/node/pull/50003",
        author="maintainer",
        description="Improve performance and throughput for native fetch implementation.",
        changed_files=[
            ChangedFile(filename="lib/internal/fetch.js", status="modified", additions=20, deletions=5)
        ],
    )

    matcher = HistoricalDecisionMatcher(seeded_db)
    matches = matcher.match(pr, threshold=0.4)

    assert len(matches) >= 1
    assert matches[0].category == MatchCategory.RELATED_DECISION


def test_4_no_relevant_decisions_found(seeded_db):
    """Verify that an unrelated PR produces no matches and report indicates absence of conflicts."""
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50004,
        title="Update documentation typography in contributing guide",
        url="https://github.com/nodejs/node/pull/50004",
        author="docs-team",
        description="Fix markdown formatting and spelling errors in doc/api/assert.md.",
        changed_files=[
            ChangedFile(filename="doc/api/assert.md", status="modified", additions=2, deletions=2)
        ],
    )

    matcher = HistoricalDecisionMatcher(seeded_db)
    matches = matcher.match(pr, threshold=0.5)

    assert len(matches) == 0
    report = generate_radar_report(pr, matches)
    assert report.has_relevant_decisions is False
    assert any("No relevant historical" in r for r in report.recommendations)


def test_5_threshold_filtering(seeded_db):
    """Verify that raising threshold filters out low-confidence matches."""
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50005,
        title="Minor fetch utility fix",
        url="https://github.com/nodejs/node/pull/50005",
        author="contributor",
        description="Tiny patch.",
        changed_files=[],
    )

    matcher = HistoricalDecisionMatcher(seeded_db)
    # Threshold 0.95 should filter out weak matches
    matches = matcher.match(pr, threshold=0.95)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_6_analyzer_rejects_issue_url():
    """Verify analyzer raises InvalidGitHubURLException if an issue URL is passed."""
    analyzer = PullRequestAnalyzer()
    with pytest.raises(InvalidGitHubURLException):
        await analyzer.analyze_url("https://github.com/nodejs/node/issues/100")


@pytest.mark.asyncio
async def test_7_analyzer_parses_pr_and_files():
    """Verify analyzer fetches metadata and files using GitHubClient."""
    mock_client = MagicMock()
    mock_client.fetch_pull_request = AsyncMock(
        return_value={
            "title": "Implement Fetch",
            "html_url": "https://github.com/nodejs/node/pull/41749",
            "body": "PR description text",
            "user": {"login": "mcollina"},
        }
    )
    mock_client.fetch_pull_request_files = AsyncMock(
        return_value=[
            {
                "filename": "lib/fetch.js",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "patch": "@@ +1,5 @@",
            }
        ]
    )

    analyzer = PullRequestAnalyzer(github_client=mock_client)
    pr = await analyzer.analyze_url("https://github.com/nodejs/node/pull/41749")

    assert pr.repository == "nodejs/node"
    assert pr.pr_number == 41749
    assert pr.title == "Implement Fetch"
    assert len(pr.changed_files) == 1
    assert pr.changed_files[0].filename == "lib/fetch.js"


def test_8_radar_report_recommendations():
    """Verify report includes actionable developer recommendations."""
    pr = PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50001,
        title="Re-add node-fetch",
        url="https://github.com/nodejs/node/pull/50001",
        author="dev",
        description="Propose node-fetch.",
        changed_files=[],
    )
    match = HistoricalMatch(
        decision_id="dec-41749-1",
        adr_id="ADR-41749-01",
        decision_summary="Adopt Undici for Fetch API",
        discussion_url="https://github.com/nodejs/node/pull/41749",
        category=MatchCategory.PREVIOUSLY_REJECTED_APPROACH,
        relevance_explanation="node-fetch was previously rejected",
        related_changed_files=[],
        evidence_references=[],
        confidence=0.9,
    )

    report = generate_radar_report(pr, [match])
    assert report.has_relevant_decisions is True
    assert report.previously_rejected_count == 1
    assert any("rejected alternative" in rec for rec in report.recommendations)
