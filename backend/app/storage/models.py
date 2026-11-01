"""Storage entity models and row definitions (Module 9)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RepositoryRecord(BaseModel):
    """Persisted GitHub repository entity."""

    repository: str  # "owner/repo"
    owner: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DiscussionRecord(BaseModel):
    """Persisted GitHub discussion (Issue or PR)."""

    id: str  # "owner/repo#entity_number"
    repository: str
    entity_number: int
    resource_type: str  # "issue" or "pull_request"
    title: str
    state: str
    author: str
    html_url: str
    body: str = ""
    created_at: str
    updated_at: str


class CommentRecord(BaseModel):
    """Persisted discussion comment with provenance."""

    comment_id: str
    discussion_id: str
    author: str
    author_association: str
    body: str
    html_url: str
    created_at: str


class DecisionRecord(BaseModel):
    """Persisted engineering decision."""

    decision_id: str  # e.g. "dec-41749-1"
    discussion_id: str
    decision_summary: str
    status: str  # "accepted", "rejected", "proposed", etc.
    confidence: float
    model_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimRecord(BaseModel):
    """Persisted rationale or argument claim."""

    decision_id: str
    claim_type: str  # "rationale", "supporting_argument", "opposing_argument", "trade_off", "consequence"
    statement: str
    confidence: float
    evidence_status: str
    supporting_comment_ids: str  # JSON list string


class AlternativeRecord(BaseModel):
    """Persisted rejected alternative."""

    decision_id: str
    title: str
    rejection_reason: str
    confidence: float
    verification_status: str
    supporting_comment_ids: str  # JSON list string


class VerificationRecord(BaseModel):
    """Persisted claim verification result."""

    decision_id: str
    claim_id: str
    claim_type: str
    claim_text: str
    status: str
    evidence_type: str
    supporting_comment_ids: str  # JSON list string
    contradicting_comment_ids: str  # JSON list string
    explanation: str
    confidence: float


class ADRRecord(BaseModel):
    """Persisted Architecture Decision Record."""

    adr_id: str  # e.g. "ADR-41749-01"
    decision_id: str
    discussion_id: str
    title: str
    status: str
    date: str
    context: str
    problem_statement: str
    decision: str
    file_slug: str
    markdown_content: str
    json_content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

