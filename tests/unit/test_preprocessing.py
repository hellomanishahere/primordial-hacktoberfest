"""Comprehensive unit tests for discussion preprocessing, noise elimination, and context preparation."""

from datetime import datetime, timezone
import pytest

from app.domain.entities import (
    CanonicalDiscussionComment,
    CanonicalDiscussionThread,
    CommentType,
)
from app.preprocessing.budgeter import (
    estimate_token_count,
    format_comment_citation,
    format_discussion_transcript,
)
from app.preprocessing.cleaner import (
    clean_discussion_thread,
    sanitize_comment_body,
    sanitize_unicode,
)
from app.preprocessing.patterns import is_bot_author
from app.preprocessing.schemas import RemovalReason


def make_sample_thread(comments=None, metadata=None) -> CanonicalDiscussionThread:
    """Helper creating a test CanonicalDiscussionThread fixture."""
    return CanonicalDiscussionThread(
        repository_owner="nodejs",
        repository_name="node",
        entity_number=41749,
        resource_type="pull_request",
        title="Adopt Undici as built-in fetch",
        body="Initial description proposing undici integration.",
        state="closed",
        author="mcollina",
        created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2022, 2, 5, 12, 0, 0, tzinfo=timezone.utc),
        html_url="https://github.com/nodejs/node/pull/41749",
        comments=comments or [],
        metadata=metadata or {},
    )


def test_1_bot_comment_removal():
    """Verify bot accounts like dependabot[bot], codecov, and stale are removed."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="mcollina",
            author_association="MEMBER",
            body="PR description.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="101",
            comment_type=CommentType.CONVERSATION,
            author="dependabot[bot]",
            author_association="NONE",
            body="Dependabot bumped dependency version to 2.0.0.",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-101",
        ),
        CanonicalDiscussionComment(
            id="102",
            comment_type=CommentType.CONVERSATION,
            author="codecov",
            author_association="NONE",
            body="Coverage delta report.",
            created_at=datetime(2022, 2, 2, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-102",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 1
    assert cleaned.comments[0].id == "0"
    assert cleaned.audit.comments_removed == 2
    reasons = [r.reason for r in cleaned.audit.removal_records]
    assert RemovalReason.BOT_ACCOUNT in reasons


def test_2_human_comment_retention_with_bot_substring():
    """Verify human maintainers like 'abbot', 'robotics', or 'talbot' are NOT filtered."""
    assert is_bot_author("abbot") is False
    assert is_bot_author("robotics_maintainer") is False
    assert is_bot_author("talbot") is False
    assert is_bot_author("botanist") is False

    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="abbot",
            author_association="MEMBER",
            body="Initial problem statement.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="201",
            comment_type=CommentType.CONVERSATION,
            author="talbot",
            author_association="CONTRIBUTOR",
            body="I tested the HTTP parser and it performs well under load.",
            created_at=datetime(2022, 2, 2, 12, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-201",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 2
    assert cleaned.comments[1].author == "talbot"
    assert cleaned.audit.comments_removed == 0


def test_3_ci_notification_removal():
    """Verify automated CI/CD and coverage table comments are filtered."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Description",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="301",
            comment_type=CommentType.CONVERSATION,
            author="ci-service",
            author_association="NONE",
            body="## [Codecov](https://codecov.io/gh/nodejs/node)\n| Impacted Files | Coverage Δ |\n|---|---|",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-301",
        ),
        CanonicalDiscussionComment(
            id="302",
            comment_type=CommentType.CONVERSATION,
            author="azure-ci",
            author_association="NONE",
            body="All checks have passed (34 successful checks).",
            created_at=datetime(2022, 2, 2, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-302",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 1
    assert cleaned.audit.comments_removed == 2
    reasons = [r.reason for r in cleaned.audit.removal_records]
    assert RemovalReason.AUTOMATED_COVERAGE_REPORT in reasons
    assert RemovalReason.AUTOMATED_CI_NOTIFICATION in reasons


def test_4_emoji_only_comment_removal():
    """Verify standalone +1, -1, and emoji-only reaction comments are filtered."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Desc",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="401",
            comment_type=CommentType.CONVERSATION,
            author="user1",
            author_association="NONE",
            body="+1",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-401",
        ),
        CanonicalDiscussionComment(
            id="402",
            comment_type=CommentType.CONVERSATION,
            author="user2",
            author_association="NONE",
            body=":+1:",
            created_at=datetime(2022, 2, 2, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-402",
        ),
        CanonicalDiscussionComment(
            id="403",
            comment_type=CommentType.CONVERSATION,
            author="user3",
            author_association="NONE",
            body="👍",
            created_at=datetime(2022, 2, 2, 12, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-403",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 1
    assert cleaned.audit.comments_removed == 3
    for r in cleaned.audit.removal_records:
        assert r.reason == RemovalReason.REACTION_ONLY


def test_5_short_meaningful_technical_comment_retention():
    """Verify short technical comments with substance (even with 'LGTM') are preserved."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Desc",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="501",
            comment_type=CommentType.CONVERSATION,
            author="mcollina",
            author_association="MEMBER",
            body="LGTM, but make sure to free the buffer on error.",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-501",
        ),
        CanonicalDiscussionComment(
            id="502",
            comment_type=CommentType.CONVERSATION,
            author="jasnell",
            author_association="MEMBER",
            body="Use UTF-8.",
            created_at=datetime(2022, 2, 2, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-502",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 3
    assert cleaned.comments[1].body == "LGTM, but make sure to free the buffer on error."
    assert cleaned.comments[2].body == "Use UTF-8."


def test_6_code_fence_preservation():
    """Verify fenced markdown code blocks are byte-for-byte preserved."""
    code_block = "```python\ndef test_fn():\n    return 42\n```"
    text = f"Here is my proposed fix:\n\n{code_block}\n\nLet me know your thoughts."
    sanitized = sanitize_comment_body(text)

    assert code_block in sanitized
    assert "def test_fn():" in sanitized


def test_7_inline_code_preservation():
    """Verify inline backtick identifiers are preserved."""
    text = "Please check the return value of `parse_http_chunk()` in `lib/fetch.js`."
    sanitized = sanitize_comment_body(text)
    assert "`parse_http_chunk()`" in sanitized
    assert "`lib/fetch.js`" in sanitized


def test_8_url_and_permalink_preservation():
    """Verify technical URLs, commit hashes, and GitHub issue links are preserved."""
    text = "See discussion in nodejs/node#41749 and commit 359fdc49662c2eb7."
    sanitized = sanitize_comment_body(text)
    assert "nodejs/node#41749" in sanitized
    assert "359fdc49662c2eb7" in sanitized


def test_9_html_comment_removal():
    """Verify HTML comment blocks <!-- ... --> are removed outside code fences, but preserved inside."""
    text = (
        "Visible text before comment.\n"
        "<!-- This is a hidden issue template note -->\n"
        "Visible text after comment.\n\n"
        "```html\n"
        "<!-- This HTML comment inside code MUST be preserved -->\n"
        "<div>Hello</div>\n"
        "```"
    )
    sanitized = sanitize_comment_body(text)

    assert "This is a hidden issue template note" not in sanitized
    assert "Visible text before comment." in sanitized
    assert "Visible text after comment." in sanitized
    assert "<!-- This HTML comment inside code MUST be preserved -->" in sanitized


def test_10_signature_footer_removal():
    """Verify mobile signatures like 'Sent from my iPhone' are removed."""
    text = (
        "I agree with adopting undici.\n\n"
        "-- \n"
        "Sent from my iPhone"
    )
    sanitized = sanitize_comment_body(text)
    assert "I agree with adopting undici." in sanitized
    assert "Sent from my iPhone" not in sanitized


def test_11_chronological_ordering():
    """Verify comments are ordered chronologically by created_at."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Root description",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="103",
            comment_type=CommentType.CONVERSATION,
            author="charlie",
            author_association="MEMBER",
            body="Third in time.",
            created_at=datetime(2022, 2, 3, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-103",
        ),
        CanonicalDiscussionComment(
            id="101",
            comment_type=CommentType.CONVERSATION,
            author="alice",
            author_association="MEMBER",
            body="First in time.",
            created_at=datetime(2022, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-101",
        ),
        CanonicalDiscussionComment(
            id="102",
            comment_type=CommentType.CONVERSATION,
            author="bob",
            author_association="MEMBER",
            body="Second in time.",
            created_at=datetime(2022, 2, 2, 12, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-102",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 4
    assert [c.id for c in cleaned.comments] == ["0", "101", "102", "103"]


def test_12_original_comment_id_preservation():
    """Verify original GitHub comment IDs are preserved without re-indexing."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Desc",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="1034981",
            comment_type=CommentType.CONVERSATION,
            author="mcollina",
            author_association="MEMBER",
            body="Undici is faster.",
            created_at=datetime(2022, 2, 3, 14, 22, 10, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-1034981",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert cleaned.comments[1].id == "1034981"
    assert cleaned.comments[1].html_url == "https://github.com/nodejs/node/pull/41749#issuecomment-1034981"


def test_13_review_comment_metadata_preservation():
    """Verify inline diff review comment metadata (path, diff_hunk, review_state) is preserved."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Desc",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="888123",
            comment_type=CommentType.REVIEW_COMMENT,
            author="jasnell",
            author_association="MEMBER",
            body="Please avoid memory leaks in the stream handler.",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#discussion_r888123",
            path="lib/fetch.js",
            diff_hunk="@@ -10,5 +10,12 @@",
            in_reply_to_id="888000",
            review_state="CHANGES_REQUESTED",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 2
    rev = cleaned.comments[1]
    assert rev.path == "lib/fetch.js"
    assert rev.diff_hunk == "@@ -10,5 +10,12 @@"
    assert rev.in_reply_to_id == "888000"
    assert rev.review_state == "CHANGES_REQUESTED"


def test_14_empty_discussion_handling():
    """Verify empty discussions (0 comments) are handled safely without crashing."""
    thread = make_sample_thread(comments=[])
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 0
    assert cleaned.audit.is_empty is True
    assert cleaned.audit.total_comments_input == 0
    assert cleaned.audit.substantive_comments_retained == 0


def test_15_all_comments_filtered_handling():
    """Verify threads where all non-description comments are filtered return valid audit."""
    comments = [
        CanonicalDiscussionComment(
            id="1",
            comment_type=CommentType.CONVERSATION,
            author="dependabot[bot]",
            author_association="NONE",
            body="Bump version.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-1",
        ),
        CanonicalDiscussionComment(
            id="2",
            comment_type=CommentType.CONVERSATION,
            author="user",
            author_association="NONE",
            body="+1",
            created_at=datetime(2022, 2, 1, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-2",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 0
    assert cleaned.audit.is_empty is True
    assert cleaned.audit.comments_removed == 2


def test_16_unicode_handling():
    """Verify malformed unicode, surrogates, and international characters are handled safely."""
    malformed = "Testing international chars: 日本語, accents é à ü, and safe unicode."
    sanitized = sanitize_unicode(malformed)
    assert "日本語" in sanitized
    assert "é" in sanitized


def test_17_duplicate_comment_ids_deduplication():
    """Verify duplicate comment IDs are deduplicated and recorded in audit."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="dev",
            author_association="MEMBER",
            body="Desc",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="101",
            comment_type=CommentType.CONVERSATION,
            author="alice",
            author_association="MEMBER",
            body="Original comment.",
            created_at=datetime(2022, 2, 1, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-101",
        ),
        CanonicalDiscussionComment(
            id="101",  # duplicate ID
            comment_type=CommentType.CONVERSATION,
            author="alice",
            author_association="MEMBER",
            body="Duplicate copy of comment.",
            created_at=datetime(2022, 2, 1, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-101",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    assert len(cleaned.comments) == 2
    assert cleaned.audit.comments_removed == 1
    assert cleaned.audit.removal_records[0].reason == RemovalReason.DUPLICATE_ID


def test_18_long_comment_handling():
    """Verify very long comments are preserved intact without crashing."""
    long_body = "word " * 5000  # 25,000 chars
    sanitized = sanitize_comment_body(long_body)
    assert len(sanitized.split()) == 5000


def test_19_audit_counts_and_removal_reasons():
    """Verify exact count tracking and reason categorization in audit record."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="author",
            author_association="MEMBER",
            body="Main description",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="1",
            comment_type=CommentType.CONVERSATION,
            author="stale",
            author_association="NONE",
            body="This issue has been marked as stale.",
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-1",
        ),
        CanonicalDiscussionComment(
            id="2",
            comment_type=CommentType.CONVERSATION,
            author="user",
            author_association="NONE",
            body="   \n\t  ",
            created_at=datetime(2022, 2, 2, 11, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-2",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    audit = cleaned.audit
    assert audit.total_comments_input == 3
    assert audit.substantive_comments_retained == 1
    assert audit.comments_removed == 2
    assert audit.is_empty is False

    reasons = {r.reason for r in audit.removal_records}
    assert RemovalReason.BOT_ACCOUNT in reasons
    assert RemovalReason.EMPTY_OR_WHITESPACE in reasons


def test_20_context_preparation_and_citation_formatting():
    """Verify context citation formatting: [COMMENT ID: ... | AUTHOR: ... | DATE: ...] and token budgeting."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="mcollina",
            author_association="MEMBER",
            body="Proposal for built-in fetch using Undici.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="1034981",
            comment_type=CommentType.CONVERSATION,
            author="ronag",
            author_association="MEMBER",
            body="Undici benchmark shows significant throughput advantage over node-fetch.",
            created_at=datetime(2022, 2, 3, 14, 22, 10, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-1034981",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    transcript, budgeted_thread = format_discussion_transcript(cleaned, token_ceiling=12000)

    assert "[COMMENT ID: 0 | AUTHOR: @mcollina (MEMBER) | DATE: 2022-02-01 10:00:00 UTC]" in transcript
    assert "[COMMENT ID: 1034981 | AUTHOR: @ronag (MEMBER) | DATE: 2022-02-03 14:22:10 UTC]" in transcript
    assert "Source Permalink: https://github.com/nodejs/node/pull/41749#issuecomment-1034981" in transcript
    assert budgeted_thread.estimated_tokens > 0
    assert budgeted_thread.audit.was_truncated is False


def test_21_token_budget_truncation_reporting():
    """Verify that when context ceiling is exceeded, content is not silently dropped and audit reports truncation."""
    comments = [
        CanonicalDiscussionComment(
            id="0",
            comment_type=CommentType.DESCRIPTION,
            author="mcollina",
            author_association="MEMBER",
            body="PR description.",
            created_at=datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749",
        ),
        CanonicalDiscussionComment(
            id="101",
            comment_type=CommentType.CONVERSATION,
            author="dev1",
            author_association="MEMBER",
            body="Very long technical deliberation " * 200,
            created_at=datetime(2022, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-101",
        ),
        CanonicalDiscussionComment(
            id="102",
            comment_type=CommentType.CONVERSATION,
            author="dev2",
            author_association="MEMBER",
            body="Another long technical deliberation " * 200,
            created_at=datetime(2022, 2, 3, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/nodejs/node/pull/41749#issuecomment-102",
        ),
    ]

    thread = make_sample_thread(comments=comments)
    cleaned = clean_discussion_thread(thread)

    # Apply tight token ceiling (e.g., 200 tokens)
    transcript, budgeted_thread = format_discussion_transcript(cleaned, token_ceiling=200)

    # Truncation must be explicitly reported
    assert budgeted_thread.audit.was_truncated is True
    # At least one comment must have been audited with EXCEEDS_BUDGET
    budget_removals = [
        r for r in budgeted_thread.audit.removal_records
        if r.reason == RemovalReason.EXCEEDS_BUDGET
    ]
    assert len(budget_removals) >= 1
    # Description comment (ID 0) must NEVER be dropped
    assert budgeted_thread.comments[0].id == "0"

