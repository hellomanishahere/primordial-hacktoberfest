"""Canonical Pydantic domain models and API schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    """Lifecycle status of a recovered architectural decision."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class OptionStatus(str, Enum):
    """Evaluation status of a specific design alternative."""

    CHOSEN = "chosen"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"


class ExtractRequest(BaseModel):
    """Payload for initiating synchronous decision recovery."""

    url: str = Field(..., description="Public GitHub Issue or Pull Request URL", json_schema_extra={"example": "https://github.com/nodejs/node/pull/41749"})
    force_refresh: bool = Field(default=False, description="Bypass cached extraction results if previously persisted")


class ChosenOption(BaseModel):
    """Accepted architectural solution."""

    name: str = Field(..., description="Name of the accepted solution")
    description: str = Field(..., description="Technical explanation of the solution")
    evidence_ids: List[str] = Field(default_factory=list, description="GitHub comment IDs directly supporting this choice")


class ConsideredOption(BaseModel):
    """Evaluated alternative design proposal."""

    name: str = Field(..., description="Name of evaluated option")
    status: OptionStatus = Field(..., description="Option evaluation status")
    rejection_reason: Optional[str] = Field(default=None, description="Explicit technical rationale for rejection, or null if unstated")
    evidence_ids: List[str] = Field(default_factory=list, description="GitHub comment IDs where this alternative was evaluated")


class Consequences(BaseModel):
    """Architectural trade-offs resulting from the decision."""

    positive: List[str] = Field(default_factory=list, description="Explicit benefits or gains identified in deliberation")
    negative: List[str] = Field(default_factory=list, description="Explicit trade-offs, risks, or liabilities accepted")


class DecisionPayload(BaseModel):
    """Decomposed, structured representation of an architectural decision."""

    title: str = Field(..., description="Active-voice architectural decision title")
    status: DecisionStatus = Field(..., description="Standardized decision status")
    context_and_problem: str = Field(..., description="Problem description and motivating context")
    decision_drivers: List[str] = Field(default_factory=list, description="Key architectural drivers or constraints")
    chosen_option: Optional[ChosenOption] = Field(default=None, description="The accepted solution, or null if unresolved")
    considered_options: List[ConsideredOption] = Field(default_factory=list, description="Alternative options evaluated during discussion")
    consequences: Consequences = Field(default_factory=Consequences, description="Architectural consequences and trade-offs")


class EvidenceItem(BaseModel):
    """Verifiable link between an architectural claim and an authentic GitHub comment."""

    comment_id: str = Field(..., description="Authentic GitHub comment ID")
    author: str = Field(..., description="GitHub username of the comment author")
    timestamp: datetime = Field(..., description="Timestamp of the comment creation")
    html_url: str = Field(..., description="Direct permalink to the comment on GitHub")
    claim_supported: str = Field(..., description="Summary of the architectural claim supported")
    verbatim_excerpt: Optional[str] = Field(default=None, description="Direct textual citation from the comment")
    is_technically_verified: bool = Field(default=True, description="Level 1 verification badge confirming physical ID existence")


class ClassificationResult(BaseModel):
    """Stage 1 binary decision gate assessment."""

    is_decision: bool = Field(..., description="Whether the thread contains an architectural decision")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Internal model confidence heuristic")
    reasoning: str = Field(..., description="Concise rationale for classification outcome")


class ContextProcessingMetadata(BaseModel):
    """Metadata regarding transcript preprocessing and token budgeting."""

    total_comments_ingested: int = Field(..., description="Total raw comments retrieved from GitHub")
    substantive_comments_retained: int = Field(..., description="Comments retained after bot and noise filtering")
    was_truncated: bool = Field(..., description="Whether chronological context budgeting truncated comments")
    processing_note: Optional[str] = Field(default=None, description="Diagnostic notes on context processing")


class VerifiedDecisionResponse(BaseModel):
    """Canonical API response envelope for decision extraction."""

    extraction_id: str = Field(..., description="Unique extraction identifier")
    repository: str = Field(..., description="Target repository in owner/repo format")
    source_url: str = Field(..., description="Original GitHub discussion URL")
    entity_type: str = Field(..., description="Entity type: issue or pull_request")
    entity_number: int = Field(..., description="GitHub issue or pull request number")
    extracted_at: datetime = Field(..., description="UTC extraction timestamp")
    classification: ClassificationResult = Field(..., description="Stage 1 decision classification")
    decision: Optional[DecisionPayload] = Field(default=None, description="Structured decision record if detected")
    evidence_catalog: List[EvidenceItem] = Field(default_factory=list, description="Level 1 verified evidence citations")
    context_metadata: ContextProcessingMetadata = Field(..., description="Transcript processing and budget statistics")
    madr_content: Optional[str] = Field(default=None, description="Rendered MADR 3.0.0 Markdown document")


class ComponentHealth(BaseModel):
    """Health status of an external or backing dependency."""

    status: str = Field(..., description="Status string: ok, available, degraded, or unreachable", json_schema_extra={"example": "ok"})
    details: Optional[str] = Field(default=None, description="Diagnostic status details", json_schema_extra={"example": "SQLite WAL mode enabled"})
    url: Optional[str] = Field(default=None, description="Optional target service URL", json_schema_extra={"example": "http://localhost:11434"})


class HealthResponse(BaseModel):
    """API health check response matching Document 05 Section 5."""

    status: str = Field(..., description="Overall service status", json_schema_extra={"example": "ok"})
    app: str = Field(..., description="Application name", json_schema_extra={"example": "Primordial"})
    version: str = Field(..., description="Application version", json_schema_extra={"example": "0.1.0"})
    environment: str = Field(..., description="Active runtime environment", json_schema_extra={"example": "development"})
    database: ComponentHealth = Field(..., description="SQLite database connectivity verification")
    ollama: ComponentHealth = Field(..., description="Local Ollama service availability verification")

