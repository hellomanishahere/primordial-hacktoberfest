"""Internal dataclasses and enumeration entities."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CommentType(str, Enum):
    """Categorization of ingested GitHub discussion comments."""

    DESCRIPTION = "description"
    CONVERSATION = "conversation"
    REVIEW_COMMENT = "review_comment"
    REVIEW_BODY = "review_body"
    REVIEW_SUMMARY = "review_summary"


@dataclass
class CanonicalDiscussionComment:
    """Canonical representation of an individual comment within a GitHub discussion."""

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert comment to JSON-serializable dictionary."""
        data = asdict(self)
        data["comment_type"] = self.comment_type.value
        data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class CanonicalDiscussionThread:
    """Canonical representation of a complete ingested GitHub discussion thread."""

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
    comments: List[CanonicalDiscussionComment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def repository(self) -> str:
        """Full repository name in owner/repo format."""
        return f"{self.repository_owner}/{self.repository_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert thread and all contained comments to JSON-serializable dictionary."""
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
            "metadata": self.metadata,
        }
