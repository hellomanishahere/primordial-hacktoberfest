"""Context preparation, token budgeting, and citation-formatted transcript generation."""

import math
from typing import List, Optional, Tuple

from app.preprocessing.schemas import (
    CleanedDiscussionComment,
    CleanedDiscussionThread,
    CommentRemovalRecord,
    RemovalReason,
)

DEFAULT_TOKEN_CEILING = 12000


def estimate_token_count(text: Optional[str]) -> int:
    """
    Estimates token count using a conservative character-and-word heuristic.
    Rule: 1 word ≈ 1.33 tokens; 4 characters ≈ 1 token.
    Safe for llama/qwen tokenizers without requiring heavy tokenization dependencies.
    """
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    return int(math.ceil(max(words * 1.33, chars / 4.0)))


def format_comment_citation(comment: CleanedDiscussionComment) -> str:
    """
    Produces a structured, provenance-rich citation block for a single comment.

    Format:
    [COMMENT ID: ... | AUTHOR: ... | DATE: ...]
    {body}
    Source Permalink: {html_url}
    """
    dt_str = (
        comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if comment.created_at
        else "UNKNOWN DATE"
    )
    header = f"[COMMENT ID: {comment.id} | AUTHOR: @{comment.author} ({comment.author_association}) | DATE: {dt_str}]"

    parts = [header]

    if comment.path:
        parts.append(f"File: {comment.path}")

    if comment.diff_hunk:
        parts.append(f"Diff Context:\n{comment.diff_hunk}")

    if comment.review_state:
        parts.append(f"Review Verdict: {comment.review_state}")

    parts.append(comment.body if comment.body else "(Empty comment)")
    parts.append(f"Source Permalink: {comment.html_url}")

    return "\n".join(parts)


def format_discussion_transcript(
    thread: CleanedDiscussionThread,
    token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
) -> Tuple[str, CleanedDiscussionThread]:
    """
    Compiles a CleanedDiscussionThread into a chronological, citation-formatted transcript.

    If token_ceiling is specified and the thread exceeds it:
    - ID "0" (Description) is strictly preserved.
    - Subsequent comments are included chronologically while remaining within the ceiling.
    - Excluded comments are explicitly audited with RemovalReason.EXCEEDS_BUDGET.
    - thread.audit.was_truncated is set to True.
    - Never silently truncates content.

    Returns:
        Tuple of (transcript_string, updated_cleaned_discussion_thread).
    """
    if not thread.comments:
        return "", thread

    header_block = (
        f"=== REPOSITORY: {thread.repository} | {thread.resource_type.upper()} #{thread.entity_number} ===\n"
        f"TITLE: {thread.title}\n"
        f"AUTHOR: @{thread.author}\n"
        f"STATE: {thread.state}\n"
        f"PERMALINK: {thread.html_url}\n"
        "============================================================"
    )

    budget_used = estimate_token_count(header_block)

    included_comments: List[CleanedDiscussionComment] = []
    budget_removal_records: List[CommentRemovalRecord] = []
    transcript_blocks: List[str] = [header_block]

    for idx, comment in enumerate(thread.comments):
        citation = format_comment_citation(comment)
        comment_tokens = estimate_token_count(citation)

        is_desc = (comment.id == "0")

        if token_ceiling is not None and not is_desc:
            if budget_used + comment_tokens > token_ceiling:
                # Exceeds token budget: record explicit removal in audit
                budget_removal_records.append(
                    CommentRemovalRecord(
                        comment_id=comment.id,
                        author=comment.author,
                        reason=RemovalReason.EXCEEDS_BUDGET,
                        details=(
                            f"Excluded to adhere to context ceiling ({token_ceiling} tokens). "
                            f"Comment required {comment_tokens} tokens."
                        ),
                    )
                )
                continue

        budget_used += comment_tokens
        included_comments.append(comment)
        transcript_blocks.append(citation)

    transcript_text = "\n\n".join(transcript_blocks)

    # Update thread audit if comments were excluded
    updated_audit = thread.audit
    if budget_removal_records:
        updated_audit.was_truncated = True
        updated_audit.comments_removed += len(budget_removal_records)
        updated_audit.removal_records.extend(budget_removal_records)
        updated_audit.substantive_comments_retained = len(included_comments)
        updated_audit.processing_notes.append(
            f"Context budget applied: {len(budget_removal_records)} comments excluded to fit within {token_ceiling} tokens."
        )

    updated_thread = CleanedDiscussionThread(
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
        comments=included_comments,
        audit=updated_audit,
        estimated_tokens=budget_used,
        metadata=thread.metadata,
    )

    return transcript_text, updated_thread

