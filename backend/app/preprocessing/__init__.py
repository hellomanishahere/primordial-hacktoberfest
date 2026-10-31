"""Discussion preprocessing, noise reduction, and context preparation."""

from app.preprocessing.budgeter import (
    DEFAULT_TOKEN_CEILING,
    estimate_token_count,
    format_comment_citation,
    format_discussion_transcript,
)
from app.preprocessing.cleaner import (
    classify_comment_for_removal,
    clean_discussion_thread,
    sanitize_comment_body,
    sanitize_unicode,
)
from app.preprocessing.patterns import (
    CI_NOTIFICATION_PATTERNS,
    EXCESSIVE_NEWLINES_REGEX,
    HTML_COMMENT_REGEX,
    KNOWN_BOT_ACCOUNTS,
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

__all__ = [
    # Cleaner
    "clean_discussion_thread",
    "sanitize_comment_body",
    "sanitize_unicode",
    "classify_comment_for_removal",
    # Budgeter / Formatter
    "DEFAULT_TOKEN_CEILING",
    "estimate_token_count",
    "format_comment_citation",
    "format_discussion_transcript",
    # Patterns
    "is_bot_author",
    "KNOWN_BOT_ACCOUNTS",
    "STANDALONE_REACTION_REGEX",
    "CI_NOTIFICATION_PATTERNS",
    "MOBILE_SIGNATURE_PATTERNS",
    "HTML_COMMENT_REGEX",
    "EXCESSIVE_NEWLINES_REGEX",
    # Schemas
    "RemovalReason",
    "CommentRemovalRecord",
    "PreprocessingAudit",
    "CleanedDiscussionComment",
    "CleanedDiscussionThread",
]
