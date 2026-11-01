"""Data normalization: converts heterogeneous GitHub REST API payloads into canonical representations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.entities import (
    CanonicalDiscussionComment,
    CanonicalDiscussionThread,
    CommentType,
)
from app.github.parser import GitHubTarget


def parse_iso_datetime(val: Any) -> datetime:
    """Parses an ISO 8601 string or returns current UTC datetime if unavailable."""
    if isinstance(val, datetime):
        return val
    if not val or not isinstance(val, str):
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def normalize_github_discussion(
    target: GitHubTarget,
    raw_data: Dict[str, Any],
) -> CanonicalDiscussionThread:
    """
    Transforms raw responses from GitHub issue/PR endpoints into a unified CanonicalDiscussionThread.

    Args:
        target: Validated GitHub target.
        raw_data: Dictionary containing 'metadata', 'conversation_comments',
                  'review_comments', and 'reviews'.

    Returns:
        CanonicalDiscussionThread with chronologically sorted, strongly typed comments.
    """
    metadata: Dict[str, Any] = raw_data.get("metadata") or {}
    conversation_comments: List[Dict[str, Any]] = raw_data.get("conversation_comments") or []
    review_comments: List[Dict[str, Any]] = raw_data.get("review_comments") or []
    reviews: List[Dict[str, Any]] = raw_data.get("reviews") or []

    # 1. Thread-level metadata
    author_info = metadata.get("user") or {}
    thread_author = author_info.get("login") or "unknown"
    thread_title = metadata.get("title") or ""
    thread_body = metadata.get("body") or ""
    thread_state = metadata.get("state") or "unknown"
    thread_created_at = parse_iso_datetime(metadata.get("created_at"))
    thread_updated_at = (
        parse_iso_datetime(metadata.get("updated_at"))
        if metadata.get("updated_at")
        else None
    )
    thread_html_url = metadata.get("html_url") or f"https://github.com/{target.owner}/{target.repo}/{target.entity_type}/{target.entity_number}"
    resource_type = "pull_request" if target.is_pull_request else "issue"

    # 2. Prepend original description as Comment ID "0"
    description_comment = CanonicalDiscussionComment(
        id="0",
        comment_type=CommentType.DESCRIPTION,
        author=thread_author,
        author_association=metadata.get("author_association") or "NONE",
        body=thread_body,
        created_at=thread_created_at,
        html_url=thread_html_url,
        diff_hunk=None,
        path=None,
        in_reply_to_id=None,
        review_state=None,
        updated_at=thread_updated_at,
    )

    discussion_comments: List[CanonicalDiscussionComment] = []

    # 3. Normalize Issue/PR conversational comments
    for item in conversation_comments:
        c_user = item.get("user") or {}
        comment_id = str(item.get("id"))
        created_at = parse_iso_datetime(item.get("created_at"))
        updated_at = (
            parse_iso_datetime(item.get("updated_at"))
            if item.get("updated_at")
            else None
        )
        body = item.get("body") or ""
        html_url = item.get("html_url") or f"{thread_html_url}#issuecomment-{comment_id}"

        discussion_comments.append(
            CanonicalDiscussionComment(
                id=comment_id,
                comment_type=CommentType.CONVERSATION,
                author=c_user.get("login") or "ghost",
                author_association=item.get("author_association") or "NONE",
                body=body,
                created_at=created_at,
                html_url=html_url,
                diff_hunk=None,
                path=None,
                in_reply_to_id=None,
                review_state=None,
                updated_at=updated_at,
            )
        )

    # 4. Normalize Pull Request inline review diff comments
    for item in review_comments:
        c_user = item.get("user") or {}
        comment_id = str(item.get("id"))
        created_at = parse_iso_datetime(item.get("created_at"))
        updated_at = (
            parse_iso_datetime(item.get("updated_at"))
            if item.get("updated_at")
            else None
        )
        body = item.get("body") or ""
        html_url = item.get("html_url") or f"{thread_html_url}#discussion_r{comment_id}"
        in_reply = item.get("in_reply_to_id")

        discussion_comments.append(
            CanonicalDiscussionComment(
                id=comment_id,
                comment_type=CommentType.REVIEW_COMMENT,
                author=c_user.get("login") or "ghost",
                author_association=item.get("author_association") or "NONE",
                body=body,
                created_at=created_at,
                html_url=html_url,
                diff_hunk=item.get("diff_hunk"),
                path=item.get("path"),
                in_reply_to_id=str(in_reply) if in_reply is not None else None,
                review_state=None,
                updated_at=updated_at,
            )
        )

    # 5. Normalize Pull Request review summaries
    for item in reviews:
        c_user = item.get("user") or {}
        review_id = str(item.get("id"))
        created_at = parse_iso_datetime(
            item.get("submitted_at") or item.get("created_at") or metadata.get("created_at")
        )
        body = item.get("body") or ""
        review_state = item.get("state")  # APPROVED, CHANGES_REQUESTED, COMMENTED, etc.
        html_url = item.get("html_url") or f"{thread_html_url}#pullrequestreview-{review_id}"

        # Include if review contains text body or an explicit review status verdict
        discussion_comments.append(
            CanonicalDiscussionComment(
                id=f"review_{review_id}",
                comment_type=CommentType.REVIEW_BODY,
                author=c_user.get("login") or "ghost",
                author_association=item.get("author_association") or "NONE",
                body=body,
                created_at=created_at,
                html_url=html_url,
                diff_hunk=None,
                path=None,
                in_reply_to_id=None,
                review_state=review_state,
                updated_at=None,
            )
        )

    # 6. Chronological sort (preserves discussion progression)
    discussion_comments.sort(key=lambda c: c.created_at)

    # Description (ID "0") is always placed at the start
    all_comments = [description_comment] + discussion_comments

    # 7. Collect rich metadata
    labels = [lbl.get("name") for lbl in metadata.get("labels", []) if isinstance(lbl, dict) and "name" in lbl]

    extracted_metadata = {
        "merged": metadata.get("merged", False),
        "mergeable_state": metadata.get("mergeable_state"),
        "base_branch": metadata.get("base", {}).get("ref") if isinstance(metadata.get("base"), dict) else None,
        "head_branch": metadata.get("head", {}).get("ref") if isinstance(metadata.get("head"), dict) else None,
        "labels": labels,
        "conversation_comments_count": len(conversation_comments),
        "review_comments_count": len(review_comments),
        "reviews_count": len(reviews),
    }

    return CanonicalDiscussionThread(
        repository_owner=target.owner,
        repository_name=target.repo,
        entity_number=target.entity_number,
        resource_type=resource_type,
        title=thread_title,
        body=thread_body,
        state=thread_state,
        author=thread_author,
        created_at=thread_created_at,
        updated_at=thread_updated_at,
        html_url=thread_html_url,
        comments=all_comments,
        metadata=extracted_metadata,
    )

