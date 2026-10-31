"""Pydantic schemas and domain models for Historical PR Radar (Module 10)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchCategory(str, Enum):
    """Categorization of a historical decision's relationship to the analyzed PR."""

    POTENTIAL_CONFLICT = "potential_conflict"
    RELATED_DECISION = "related_decision"
    PREVIOUSLY_REJECTED_APPROACH = "previously_rejected_approach"
    POTENTIALLY_REPEATED_DECISION = "potentially_repeated_decision"
    NO_RELEVANT_DECISION = "no_relevant_decision"


class ChangedFile(BaseModel):
    """File modified, added, or removed in a Pull Request."""

    filename: str
    status: str = "modified"  # modified, added, removed, renamed
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


class PullRequestAnalysis(BaseModel):
    """Extracted metadata, modified files, and intent of a Pull Request."""

    repository: str
    pr_number: int
    title: str
    url: str
    author: str
    description: str = ""
    changed_files: List[ChangedFile] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "pr_number": self.pr_number,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "description": self.description,
            "changed_files": [f.model_dump() for f in self.changed_files],
        }


class HistoricalMatch(BaseModel):
    """A historical decision relevant to the current PR."""

    decision_id: str
    adr_id: Optional[str] = None
    decision_summary: str
    discussion_url: str
    category: MatchCategory
    relevance_explanation: str
    related_changed_files: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "adr_id": self.adr_id,
            "decision_summary": self.decision_summary,
            "discussion_url": self.discussion_url,
            "category": self.category.value,
            "relevance_explanation": self.relevance_explanation,
            "related_changed_files": self.related_changed_files,
            "evidence_references": self.evidence_references,
            "confidence": self.confidence,
        }


class RadarReport(BaseModel):
    """Structured developer report produced by Historical PR Radar."""

    pr_info: PullRequestAnalysis
    historical_matches: List[HistoricalMatch] = Field(default_factory=list)
    potential_conflicts_count: int = 0
    previously_rejected_count: int = 0
    recommendations: List[str] = Field(default_factory=list)
    has_relevant_decisions: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pr_info": self.pr_info.to_dict(),
            "historical_matches": [m.to_dict() for m in self.historical_matches],
            "potential_conflicts_count": self.potential_conflicts_count,
            "previously_rejected_count": self.previously_rejected_count,
            "recommendations": self.recommendations,
            "has_relevant_decisions": self.has_relevant_decisions,
        }
