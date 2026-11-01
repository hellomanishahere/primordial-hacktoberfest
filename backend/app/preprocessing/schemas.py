"""Schemas and data structures for cleaned discussions and filtering audits."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.domain.entities import CommentType


class RemovalReason(str, Enum):
    """Categorized explanation for discarding a discussion comment during preprocessing."""

    BOT_ACCOUNT = "bot_account"
    EMPTY_OR_WHITESPACE = "empty_or_whitespace"
    REACTION_ONLY = "reaction_only"
    AUTOMATED_CI_NOTIFICATION = "automated_ci_notification"
    AUTOMATED_COVERAGE_REPORT = "automated_coverage_report"
    DUPLICATE_ID = "duplicate_id"
    EXCEEDS_BUDGET = "exceeds_budget"


@dataclass
class CommentRemovalRecord:
    """Record explaining why an individual comment was removed during preprocessing."""

    comment_id: str
    author: str
    reason: RemovalReason
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "author": self.author,
            "reason": self.reason.value,
            "details": self.details,
        }


@dataclass
class PreprocessingAudit:
    """Full transparency audit of preprocessing filtering decisions."""

    total_comments_input: int
    substantive_comments_retained: int
    comments_removed: int
    removal_records: List[CommentRemovalRecord] = field(default_factory=list)
    is_empty: bool = False
    was_truncated: bool = False
    input_already_truncated: bool = False
    processing_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_comments_input": self.total_comments_input,
            "substantive_comments_retained": self.substantive_comments_retained,
            "comments_removed": self.comments_removed,
            "removal_records": [r.to_dict() for r in self.removal_records],
            "is_empty": self.is_empty,
            "was_truncated": self.was_truncated,
            "input_already_truncated": self.input_already_truncated,
            "processing_notes": self.processing_notes,
        }


@dataclass
class CleanedDiscussionComment:
    """Cleaned, sanitized comment with source provenance and original ordering preserved."""

    id: str
    comment_type: CommentType
    author: str
    author_association: str
    body: str
    created_at: datetime
    html_url: str
    diff_hunk: Optional[str] = None
    path: Optional[str] = None
    in_reply_to_id: Optional[str] = None
    review_state: Optional[str] = None
    updated_at: Optional[datetime] = None
    original_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["comment_type"] = self.comment_type.value
        data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class CleanedDiscussionThread:
    """Structured cleaned discussion with full provenance and audit trail."""

    repository_owner: str
    repository_name: str
    entity_number: int
    resource_type: str  # "issue" or "pull_request"
    title: str
    body: Optional[str]
    state: str
    author: str
    created_at: datetime
    updated_at: Optional[datetime]
    html_url: str
    comments: List[CleanedDiscussionComment] = field(default_factory=list)
    audit: PreprocessingAudit = field(
        default_factory=lambda: PreprocessingAudit(0, 0, 0)
    )
    estimated_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def repository(self) -> str:
        return f"{self.repository_owner}/{self.repository_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository_owner": self.repository_owner,
            "repository_name": self.repository_name,
            "repository": self.repository,
            "entity_number": self.entity_number,
            "resource_type": self.resource_type,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "html_url": self.html_url,
            "comments": [c.to_dict() for c in self.comments],
            "total_comments": len(self.comments),
            "estimated_tokens": self.estimated_tokens,
            "audit": self.audit.to_dict(),
            "metadata": self.metadata,
        }

