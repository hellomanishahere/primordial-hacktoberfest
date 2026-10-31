"""Unit tests for GitHub discussion data normalizer."""

from datetime import datetime, timezone
import pytest
from app.domain.entities import (
    CanonicalDiscussionComment,
    CanonicalDiscussionThread,
    CommentType,
)
from app.github.normalizer import normalize_github_discussion, parse_iso_datetime
from app.github.parser import parse_github_url


def test_parse_iso_datetime_variants():
    # ISO string with UTC Z
    dt1 = parse_iso_datetime("2022-02-03T14:22:10Z")
    assert dt1.year == 2022
    assert dt1.month == 2
    assert dt1.day == 3
    assert dt1.hour == 14
    assert dt1.tzinfo is not None

    # Already a datetime
    now = datetime.now(timezone.utc)
    assert parse_iso_datetime(now) == now

    # None or empty fallback
    fallback = parse_iso_datetime(None)
    assert isinstance(fallback, datetime)


def test_normalize_pull_request_complete():
    target = parse_github_url("https://github.com/nodejs/node/pull/41749")
    raw_data = {
        "metadata": {
            "title": "Adopt Undici as built-in fetch",
            "body": "PR description detailing WHATWG standards alignment.",
            "state": "closed",
            "merged": True,
            "mergeable_state": "clean",
            "author_association": "MEMBER",
            "created_at": "2022-02-01T10:00:00Z",
            "updated_at": "2022-02-05T12:00:00Z",
            "html_url": "https://github.com/nodejs/node/pull/41749",
            "user": {"login": "mcollina"},
            "labels": [{"name": "fetch"}, {"name": "semver-minor"}],
            "base": {"ref": "main"},
            "head": {"ref": "feature/undici-fetch"},
        },
        "conversation_comments": [
            {
                "id": 1034981,
                "user": {"login": "ronag"},
                "author_association": "MEMBER",
                "body": "We should adopt Undici for performance reasons.",
                "created_at": "2022-02-03T14:22:10Z",
                "updated_at": "2022-02-03T14:25:00Z",
                "html_url": "https://github.com/nodejs/node/pull/41749#issuecomment-1034981",
            }
        ],
        "review_comments": [
            {
                "id": 888123,
                "user": {"login": "jasnell"},
                "author_association": "MEMBER",
                "body": "Check memory allocation in streaming body.",
                "created_at": "2022-02-02T11:00:00Z",  # Earlier than conversation comment!
                "html_url": "https://github.com/nodejs/node/pull/41749#discussion_r888123",
                "path": "lib/fetch.js",
                "diff_hunk": "@@ -10,5 +10,12 @@",
                "in_reply_to_id": 888000,
            }
        ],
        "reviews": [
            {
                "id": 777001,
                "user": {"login": "jasnell"},
                "author_association": "MEMBER",
                "state": "APPROVED",
                "body": "Looks great to merge after CI passes.",
                "submitted_at": "2022-02-04T09:00:00Z",
                "html_url": "https://github.com/nodejs/node/pull/41749#pullrequestreview-777001",
            }
        ],
    }

    thread: CanonicalDiscussionThread = normalize_github_discussion(target, raw_data)

    # Thread-level assertions
    assert thread.repository_owner == "nodejs"
    assert thread.repository_name == "node"
    assert thread.repository == "nodejs/node"
    assert thread.entity_number == 41749
    assert thread.resource_type == "pull_request"
    assert thread.title == "Adopt Undici as built-in fetch"
    assert thread.author == "mcollina"
    assert thread.state == "closed"
    assert thread.metadata["merged"] is True
    assert thread.metadata["labels"] == ["fetch", "semver-minor"]

    # Comment assertions (total 4 comments: description + 3 chronological comments)
    assert len(thread.comments) == 4

    # 1. First comment is always ID "0" (PR Description)
    desc = thread.comments[0]
    assert desc.id == "0"
    assert desc.comment_type == CommentType.DESCRIPTION
    assert desc.author == "mcollina"
    assert "WHATWG" in desc.body

    # 2. Chronological order verification:
    # 2022-02-02 (review comment 888123) should come BEFORE 2022-02-03 (conversation 1034981)
    rev_comm = thread.comments[1]
    assert rev_comm.id == "888123"
    assert rev_comm.comment_type == CommentType.REVIEW_COMMENT
    assert rev_comm.path == "lib/fetch.js"
    assert rev_comm.diff_hunk is not None
    assert rev_comm.in_reply_to_id == "888000"

    conv_comm = thread.comments[2]
    assert conv_comm.id == "1034981"
    assert conv_comm.comment_type == CommentType.CONVERSATION
    assert conv_comm.author == "ronag"

    rev_sum = thread.comments[3]
    assert rev_sum.id == "review_777001"
    assert rev_sum.comment_type == CommentType.REVIEW_BODY
    assert rev_sum.review_state == "APPROVED"

    # Permalinks verification
    for c in thread.comments:
        assert c.html_url.startswith("https://github.com/nodejs/node/pull/41749")


def test_normalize_empty_discussion():
    target = parse_github_url("https://github.com/owner/repo/issues/1")
    raw_data = {
        "metadata": {
            "title": "Lone Issue",
            "body": "No one commented yet",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "user": {"login": "solo-dev"},
        },
        "conversation_comments": [],
        "review_comments": [],
        "reviews": [],
    }

    thread = normalize_github_discussion(target, raw_data)
    # Only description comment exists
    assert len(thread.comments) == 1
    assert thread.comments[0].id == "0"
    assert thread.comments[0].body == "No one commented yet"


def test_normalize_handles_missing_fields_safely():
    target = parse_github_url("https://github.com/owner/repo/pull/2")
    raw_data = {
        "metadata": {},  # completely empty metadata
        "conversation_comments": [
            {
                "id": 101,
                # missing user, body, created_at, html_url
            }
        ],
    }

    thread = normalize_github_discussion(target, raw_data)
    assert thread.author == "unknown"
    assert thread.title == ""
    assert len(thread.comments) == 2
    # Check comment 101 defaulted safely
    comm = thread.comments[1]
    assert comm.id == "101"
    assert comm.author == "ghost"
    assert comm.body == ""


def test_thread_to_dict_serialization():
    target = parse_github_url("https://github.com/owner/repo/pull/5")
    raw_data = {
        "metadata": {
            "title": "Serialize test",
            "body": "Test body",
            "state": "open",
            "created_at": "2023-05-01T10:00:00Z",
            "user": {"login": "tester"},
        },
        "conversation_comments": [
            {
                "id": 1,
                "body": "Test comment",
                "created_at": "2023-05-01T11:00:00Z",
                "user": {"login": "alice"},
            }
        ],
    }

    thread = normalize_github_discussion(target, raw_data)
    dictionary = thread.to_dict()

    assert isinstance(dictionary, dict)
    assert dictionary["title"] == "Serialize test"
    assert dictionary["total_comments"] == 2
    assert isinstance(dictionary["comments"], list)
    assert dictionary["comments"][0]["id"] == "0"
    assert dictionary["comments"][1]["id"] == "1"
    assert dictionary["comments"][1]["comment_type"] == "conversation"

