"""Pydantic schemas and models for Architecture Decision Records (ADRs) (Module 8)."""

from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ADRStatus(str, Enum):
    """ADR lifecycle status adhering to MADR conventions."""

    ACCEPTED = "accepted"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    UNCLEAR = "unclear"


class ADREvidenceRef(BaseModel):
    """Traceable evidence citation pointing to a genuine GitHub discussion comment."""

    comment_id: str = Field(..., description="GitHub comment ID")
    author: str = Field(..., description="Username of comment author")
    created_at: str = Field(..., description="Comment timestamp")
    html_url: str = Field(..., description="Direct permalink URL to comment")
    quote_snippet: str = Field(..., description="Relevant textual quote")
    verification_status: str = Field(default="verified", description="Evidence verification status")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ADRAlternative(BaseModel):
    """An alternative approach considered during deliberation with rejection rationale."""

    title: str = Field(..., description="Name or summary of the alternative option")
    rejection_reason: str = Field(..., description="Explicit reason for rejection or 'Not established in discussion'")
    evidence_refs: List[ADREvidenceRef] = Field(default_factory=list, description="Citations where option was evaluated")
    verification_status: str = Field(default="verified", description="Verification status of the rejection claim")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "rejection_reason": self.rejection_reason,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs],
            "verification_status": self.verification_status,
        }


class ADRDocument(BaseModel):
    """Structured Architecture Decision Record compliant with MADR 3.0.0 conventions."""

    adr_id: str = Field(..., description="Stable predictable identifier, e.g. ADR-0001 or ADR-41749-01")
    title: str = Field(..., description="Human-readable decision record title")
    status: ADRStatus = Field(default=ADRStatus.ACCEPTED, description="Lifecycle status")
    date: str = Field(..., description="ISO or human-readable date of decision")
    context: str = Field(..., description="Technical context and background")
    problem_statement: str = Field(..., description="Specific problem or architectural need addressed")
    decision: str = Field(..., description="The chosen architectural approach or outcome")
    decision_drivers: List[str] = Field(default_factory=list, description="Forces, goals, and constraints driving the decision")
    considered_alternatives: List[ADRAlternative] = Field(default_factory=list, description="Considered options and why they were rejected")
    consequences_positive: List[str] = Field(default_factory=list, description="Positive consequences (pros/benefits)")
    consequences_negative: List[str] = Field(default_factory=list, description="Negative consequences or liabilities")
    trade_offs: List[str] = Field(default_factory=list, description="Architectural trade-offs accepted")
    supporting_evidence: List[ADREvidenceRef] = Field(default_factory=list, description="Verified citations corroborating the decision")
    contradictory_evidence: List[ADREvidenceRef] = Field(default_factory=list, description="Citations documenting objections or conflicting views")
    github_discussion_url: str = Field(..., description="Original GitHub issue/PR URL")
    repository: str = Field(..., description="Source repository in owner/repo format")
    entity_number: int = Field(..., description="GitHub Issue or PR number")
    file_slug: str = Field(..., description="Standardized filename slug, e.g. ADR-0001-adopt-undici-for-fetch")

    @classmethod
    def generate_slug(cls, adr_id: str, title: str) -> str:
        """Creates a URL-safe predictable filename slug."""
        clean_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
        slug_part = re.sub(r"[\s_]+", "-", clean_title.strip())[:50]
        return f"{adr_id.lower()}-{slug_part}".strip("-")

    def to_dict(self) -> Dict[str, Any]:
        """Converts ADR document to serializable dictionary."""
        return {
            "adr_id": self.adr_id,
            "title": self.title,
            "status": self.status.value,
            "date": self.date,
            "context": self.context,
            "problem_statement": self.problem_statement,
            "decision": self.decision,
            "decision_drivers": self.decision_drivers,
            "considered_alternatives": [alt.to_dict() for alt in self.considered_alternatives],
            "consequences_positive": self.consequences_positive,
            "consequences_negative": self.consequences_negative,
            "trade_offs": self.trade_offs,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradictory_evidence": [e.to_dict() for e in self.contradictory_evidence],
            "github_discussion_url": self.github_discussion_url,
            "repository": self.repository,
            "entity_number": self.entity_number,
            "file_slug": self.file_slug,
        }


class ADRGenerationResult(BaseModel):
    """Container for generated ADRs for a given discussion thread."""

    total_adrs: int = Field(default=0, description="Total number of ADR documents compiled")
    adrs: List[ADRDocument] = Field(default_factory=list, description="Compiled ADR documents")
    repository: str = Field(..., description="Source GitHub repository")
    entity_number: int = Field(..., description="Source GitHub Issue or PR number")
    source_url: str = Field(..., description="Original GitHub URL")
    processing_notes: List[str] = Field(default_factory=list, description="Generation and audit notes")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_adrs": self.total_adrs,
            "adrs": [a.to_dict() for a in self.adrs],
            "repository": self.repository,
            "entity_number": self.entity_number,
            "source_url": self.source_url,
            "processing_notes": self.processing_notes,
        }

