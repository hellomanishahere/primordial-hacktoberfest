"""Pydantic schemas and data contracts for AI decision detection."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateDecisionStatus(str, Enum):
    """Lifecycle status of a detected candidate engineering decision."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROPOSED = "proposed"
    DEFERRED = "deferred"
    UNCLEAR = "unclear"


class RawModelDecision(BaseModel):
    """Raw candidate decision output generated directly by the LLM."""

    decision_statement: str = Field(
        ...,
        description="Clear, declarative summary of the technical or architectural decision",
    )
    status: CandidateDecisionStatus = Field(
        ...,
        description="Status of the decision (accepted, rejected, proposed, deferred, unclear)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0",
    )
    supporting_comment_ids: List[str] = Field(
        default_factory=list,
        description="Comment IDs cited from the transcript as supporting evidence",
    )
    rationale_summary: Optional[str] = Field(
        default=None,
        description="Brief summary of why this decision was reached or rejected",
    )

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean_v = v.strip().lower()
            # Map common variations to canonical statuses
            status_map = {
                "accept": "accepted",
                "approved": "accepted",
                "adopted": "accepted",
                "reject": "rejected",
                "declined": "rejected",
                "abandoned": "rejected",
                "propose": "proposed",
                "suggestion": "proposed",
                "suggested": "proposed",
                "defer": "deferred",
                "postpone": "deferred",
                "postponed": "deferred",
                "ambiguous": "unclear",
                "uncertain": "unclear",
                "unknown": "unclear",
            }
            return status_map.get(clean_v, clean_v)
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5

    @field_validator("supporting_comment_ids", mode="before")
    @classmethod
    def normalize_comment_ids(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(item).strip() for item in v if item is not None and str(item).strip()]
        if isinstance(v, (str, int)):
            return [str(v).strip()]
        return []


class RawModelDecisionDetectionResponse(BaseModel):
    """Structured JSON response payload expected from the LLM."""

    is_decision_detected: bool = Field(
        ...,
        description="Whether any engineering decision (accepted, rejected, proposed, deferred, unclear) was detected",
    )
    decisions: List[RawModelDecision] = Field(
        ...,
        description="Strictly required list of detected candidate decisions (empty list [] if is_decision_detected is false)",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Overall analytical reasoning of the discussion deliberation",
    )


class CandidateDecision(BaseModel):
    """Validated candidate decision with verified evidence and source provenance."""

    decision_id: str = Field(
        ...,
        description="Deterministic unique identifier for the decision",
    )
    decision_statement: str = Field(
        ...,
        description="Concise, declarative summary of the technical or architectural decision",
    )
    status: CandidateDecisionStatus = Field(
        ...,
        description="Lifecycle status: accepted, rejected, proposed, deferred, or unclear",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score between 0.0 and 1.0",
    )
    supporting_comment_ids: List[str] = Field(
        ...,
        description="Verified comment IDs from the input thread providing direct evidence",
    )
    repository: str = Field(
        ...,
        description="Target GitHub repository in owner/name format",
    )
    entity_number: int = Field(
        ...,
        description="Issue or Pull Request number",
    )
    resource_type: str = Field(
        ...,
        description="Resource type ('issue' or 'pull_request')",
    )
    source_title: str = Field(
        ...,
        description="Original title of the issue or pull request",
    )
    model_name: str = Field(
        ...,
        description="Name of the AI model that performed detection",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to JSON-serializable dictionary."""
        data = self.model_dump()
        data["status"] = self.status.value
        return data


class DecisionDetectionResult(BaseModel):
    """Top-level result container for AI decision detection."""

    is_decision_detected: bool = Field(
        ...,
        description="Flag indicating if at least one validated decision was detected",
    )
    decisions: List[CandidateDecision] = Field(
        default_factory=list,
        description="List of validated candidate decisions",
    )
    total_decisions: int = Field(
        default=0,
        description="Total number of validated decisions detected",
    )
    model_name: str = Field(
        ...,
        description="Model used for decision detection",
    )
    repository: str = Field(
        ...,
        description="Target GitHub repository in owner/name format",
    )
    entity_number: int = Field(
        ...,
        description="Issue or Pull Request number",
    )
    resource_type: str = Field(
        ...,
        description="Resource type ('issue' or 'pull_request')",
    )
    source_url: str = Field(
        ...,
        description="Direct GitHub permalink to the issue or pull request",
    )
    processing_notes: List[str] = Field(
        default_factory=list,
        description="Diagnostic notes, audit trails, and evidence validation logs",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert detection result to JSON-serializable dictionary."""
        data = self.model_dump()
        data["decisions"] = [d.to_dict() for d in self.decisions]
        return data
