"""Discourse preprocessing and text sanitization for GitHub discussions."""

from datetime import datetime, timezone
import re
from typing import List, Optional, Set, Tuple
import unicodedata

from app.domain.entities import CanonicalDiscussionComment, CanonicalDiscussionThread
from app.preprocessing.patterns import (
    CI_NOTIFICATION_PATTERNS,
    EXCESSIVE_NEWLINES_REGEX,
    HTML_COMMENT_REGEX,
    MOBILE_SIGNATURE_PATTERNS,
    STANDALONE_REACTION_REGEX,
    is_bot_author,
)
from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    CommentRemovalRecord,
    PreprocessingAudit,
    RemovalReason,
)


def sanitize_unicode(text: Optional[str]) -> str:
    """
    Safely sanitizes unicode strings.
    Handles surrogates, invalid encoding, and unprintable control characters
    while preserving tabs, newlines, and carriage returns.
    """
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Safely decode surrogates and malformed bytes
    try:
        cleaned = text.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
    except Exception:
        cleaned = str(text)

    # Normalize unicode to NFC form
    cleaned = unicodedata.normalize("NFC", cleaned)

    # Strip unprintable control characters, preserving whitespace formatting
    cleaned = "".join(
        ch for ch in cleaned
        if ch in ("\t", "\n", "\r") or (unicodedata.category(ch)[0] != "C")
    )
    return cleaned


def sanitize_comment_body(raw_body: Optional[str]) -> str:
    """
    Sanitizes markdown comment text while strictly preserving:
    - Code fences (``` ... ``` or ~~~ ... ~~~)
    - Inline code (` ... `)
    - File paths, diffs, URLs, GitHub references
    Removes:
    - HTML comment blocks (<!-- ... -->) outside code fences
    - Mobile email signature footers at the end of comments
    - Excessive blank lines (3+ consecutive newlines collapsed to 2)
    """
    text = sanitize_unicode(raw_body)
    if not text.strip():
        return ""

    # Tokenize code blocks (fenced blocks or inline code) to protect them from regex modification
    code_pattern = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`)")
    tokens = code_pattern.split(text)

    sanitized_parts = []
    for token in tokens:
        if code_pattern.fullmatch(token):
            # Code block: preserve verbatim
            sanitized_parts.append(token)
        else:
            # Prose block: strip HTML comments
            prose = HTML_COMMENT_REGEX.sub("", token)
            sanitized_parts.append(prose)

    result = "".join(sanitized_parts)

    # Strip known mobile email signatures from comment end
    for sig_pattern in MOBILE_SIGNATURE_PATTERNS:
        result = sig_pattern.sub("", result)

    # Collapse excessive blank lines
    result = EXCESSIVE_NEWLINES_REGEX.sub("\n\n", result)

    return result.strip()


def classify_comment_for_removal(
    comment: CanonicalDiscussionComment,
    sanitized_body: str,
    is_description: bool = False,
) -> Optional[Tuple[RemovalReason, str]]:
    """
    Evaluates whether a comment should be removed or retained.

    Returns:
        Tuple of (RemovalReason, detailed_explanation) if removed, or None if retained.
    """
    # 1. Description (Comment ID "0") is always preserved as the foundational problem statement
    if is_description:
        return None

    # 2. Bot Author Detection
    if is_bot_author(comment.author, comment.author_association):
        return (
            RemovalReason.BOT_ACCOUNT,
            f"Author '{comment.author}' is an automated bot or service account",
        )

    # 3. Empty or Whitespace-only Comment
    if not sanitized_body.strip():
        return (
            RemovalReason.EMPTY_OR_WHITESPACE,
            "Comment body is empty or contains only whitespace after sanitization",
        )

    # Check for presence of code or technical markdown
    has_code_block = bool(re.search(r"```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`", sanitized_body))

    # 4. Standalone Reactions (+1, -1, emoji-only)
    # Comments with code blocks are never reaction noise
    if not has_code_block and STANDALONE_REACTION_REGEX.match(sanitized_body):
        return (
            RemovalReason.REACTION_ONLY,
            f"Comment is a non-substantive reaction: '{sanitized_body[:30]}'",
        )

    # 5. Automated CI/CD Notifications & Test/Coverage Reports
    if not has_code_block:
        for ci_pat in CI_NOTIFICATION_PATTERNS:
            if ci_pat.search(sanitized_body):
                pat_str = ci_pat.pattern.lower()
                if "codecov" in pat_str or "coverage" in pat_str:
                    return (
                        RemovalReason.AUTOMATED_COVERAGE_REPORT,
                        "Automated code coverage report table",
                    )
                return (
                    RemovalReason.AUTOMATED_CI_NOTIFICATION,
                    "Automated CI/CD test or build status notification",
                )

    return None


def clean_discussion_thread(
    thread: CanonicalDiscussionThread,
) -> CleanedDiscussionThread:
    """
    Transforms a CanonicalDiscussionThread into a CleanedDiscussionThread.

    Applies:
    - Bot filtering (exact and suffix detection)
    - Noise filtering (+1s, emoji reactions, automated CI/coverage tables)
    - Text sanitization (HTML comments, signatures, excess blank lines)
    - Code fence and technical identifier protection
    - Source provenance preservation
    - Filtering audit generation
    - Chronological ordering maintenance
    """
    retained_comments: List[CleanedDiscussionComment] = []
    removal_records: List[CommentRemovalRecord] = []
    seen_comment_ids: Set[str] = set()

    total_input = len(thread.comments)

    for idx, comment in enumerate(thread.comments):
        c_id = str(comment.id) if comment.id is not None else f"generated_idx_{idx}"

        # Duplicate ID check
        if c_id in seen_comment_ids:
            removal_records.append(
                CommentRemovalRecord(
                    comment_id=c_id,
                    author=comment.author or "unknown",
                    reason=RemovalReason.DUPLICATE_ID,
                    details=f"Duplicate comment ID '{c_id}' encountered at index {idx}",
                )
            )
            continue
        seen_comment_ids.add(c_id)

        is_desc = (c_id == "0")

        # Sanitize text
        sanitized_body = sanitize_comment_body(comment.body)

        # Classify for removal
        removal_verdict = classify_comment_for_removal(
            comment,
            sanitized_body=sanitized_body,
            is_description=is_desc,
        )

        if removal_verdict is not None:
            reason, details = removal_verdict
            removal_records.append(
                CommentRemovalRecord(
                    comment_id=c_id,
                    author=comment.author or "unknown",
                    reason=reason,
                    details=details,
                )
            )
            continue

        # Valid timestamp safeguard
        created_at = comment.created_at
        if not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)

        # Retain comment with full provenance
        retained_comments.append(
            CleanedDiscussionComment(
                id=c_id,
                comment_type=comment.comment_type,
                author=comment.author or "unknown",
                author_association=comment.author_association or "NONE",
                body=sanitized_body,
                created_at=created_at,
                html_url=comment.html_url or "",
                diff_hunk=comment.diff_hunk,
                path=comment.path,
                in_reply_to_id=comment.in_reply_to_id,
                review_state=comment.review_state,
                updated_at=comment.updated_at,
                original_index=idx,
            )
        )

    # Sort retained comments chronologically (excluding description which always stays at index 0)
    if retained_comments and retained_comments[0].id == "0":
        desc_comment = retained_comments[0]
        other_comments = sorted(retained_comments[1:], key=lambda c: c.created_at)
        final_comments = [desc_comment] + other_comments
    else:
        final_comments = sorted(retained_comments, key=lambda c: c.created_at)

    # Check if input source already reported truncation
    input_already_truncated = bool(thread.metadata.get("was_truncated", False))

    audit = PreprocessingAudit(
        total_comments_input=total_input,
        substantive_comments_retained=len(final_comments),
        comments_removed=len(removal_records),
        removal_records=removal_records,
        is_empty=(len(final_comments) == 0),
        was_truncated=input_already_truncated,
        input_already_truncated=input_already_truncated,
        processing_notes=[
            f"Preprocessed {total_input} comments: {len(final_comments)} retained, {len(removal_records)} removed."
        ],
    )

    # Estimate token count across retained comments
    from app.preprocessing.budgeter import estimate_token_count
    combined_text = (thread.title or "") + "\n" + "\n".join(c.body for c in final_comments)
    estimated_tokens = estimate_token_count(combined_text)

    return CleanedDiscussionThread(
        repository_owner=thread.repository_owner,
        repository_name=thread.repository_name,
        entity_number=thread.entity_number,
        resource_type=thread.resource_type,
        title=thread.title,
        body=thread.body,
        state=thread.state,
        author=thread.author,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        html_url=thread.html_url,
        comments=final_comments,
        audit=audit,
        estimated_tokens=estimated_tokens,
        metadata=thread.metadata,
    )

