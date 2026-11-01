"""Pydantic schemas and domain contracts for rationale and argument extraction."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EvidenceStatus(str, Enum):
    """Grounding verification status of an extracted claim or argument."""

    VERIFIED = "verified"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED = "unsupported"


class ExtractedClaim(BaseModel):
    """An individual extracted claim, argument, trade-off, or consequence."""

    statement: str = Field(
        ...,
        description="The substantive statement or claim extracted from discussion",
    )
    supporting_comment_ids: List[str] = Field(
        default_factory=list,
        description="Comment IDs from the transcript providing direct textual evidence",
    )
    evidence_explanation: str = Field(
        ...,
        description="Explanation of how the cited comments substantiate the claim",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this specific claim between 0.0 and 1.0",
    )
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.VERIFIED,
        description="Verification state of the evidence citations",
    )

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

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["evidence_status"] = self.evidence_status.value
        return data


class RejectedAlternative(BaseModel):
    """An alternative solution or approach that was explicitly rejected or superseded."""

    statement: str = Field(
        ...,
        description="Name or description of the rejected alternative approach",
    )
    rejection_reason: str = Field(
        ...,
        description="Explicit technical rationale for rejecting this option, or 'insufficient_evidence'",
    )
    supporting_comment_ids: List[str] = Field(
        default_factory=list,
        description="Comment IDs from the transcript where this alternative was evaluated and dismissed",
    )
    evidence_explanation: str = Field(
        ...,
        description="Explanation of evidence supporting the alternative's rejection",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.VERIFIED,
        description="Verification state of the evidence citations",
    )

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

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["evidence_status"] = self.evidence_status.value
        return data


class RawDecisionRationale(BaseModel):
    """Raw structured rationale and argument extraction for a single decision from the LLM."""

    decision_id: str = Field(
        ...,
        description="ID of the candidate decision being analyzed",
    )
    decision_summary: str = Field(
        ...,
        description="Declarative summary of the decision",
    )
    rationale: ExtractedClaim = Field(
        ...,
        description="Primary rationale explaining why this decision was reached or rejected",
    )
    supporting_arguments: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Arguments advocating for the chosen or proposed decision",
    )
    opposing_arguments: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Arguments objecting to or raising concerns against the decision",
    )
    rejected_alternatives: List[RejectedAlternative] = Field(
        default_factory=list,
        description="Alternative approaches considered but declined, with documented reasons",
    )
    trade_offs: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Compromises, architectural trade-offs, or accepted constraints",
    )
    consequences: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Immediate or long-term consequences of adopting this decision",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Overall model confidence for this extraction",
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Optional notes on evidence sufficiency or deliberation context",
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.85


class RawRationaleExtractionResponse(BaseModel):
    """Expected top-level JSON response payload from the LLM."""

    is_rationale_extracted: bool = Field(
        ...,
        description="Strictly required boolean: true if rationale was extracted, false otherwise",
    )
    rationales: List[RawDecisionRationale] = Field(
        ...,
        description="Strictly required list of extracted rationale records for each decision",
    )
    deliberation_summary: Optional[str] = Field(
        default=None,
        description="High-level overview of the discussion deliberation",
    )


class ExtractedDecisionRationale(BaseModel):
    """Validated rationale record for a decision with verified evidence grounding."""

    decision_id: str = Field(
        ...,
        description="ID of the detected decision (matching Module 4 candidate decision)",
    )
    decision_summary: str = Field(
        ...,
        description="Declarative summary of the decision",
    )
    status: str = Field(
        default="accepted",
        description="Lifecycle status of the decision (accepted, rejected, proposed, etc.)",
    )
    rationale: ExtractedClaim = Field(
        ...,
        description="Validated core rationale explaining why the decision was reached",
    )
    supporting_arguments: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Verified arguments supporting the decision",
    )
    opposing_arguments: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Verified arguments challenging or objecting to the decision",
    )
    rejected_alternatives: List[RejectedAlternative] = Field(
        default_factory=list,
        description="Verified alternative options that were evaluated and rejected",
    )
    trade_offs: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Verified architectural compromises and trade-offs",
    )
    consequences: List[ExtractedClaim] = Field(
        default_factory=list,
        description="Verified downstream consequences and technical outcomes",
    )
    evidence_comment_ids: List[str] = Field(
        default_factory=list,
        description="Aggregate of all unique genuine comment IDs cited across all verified claims",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score based on evidence strength",
    )
    extraction_notes: List[str] = Field(
        default_factory=list,
        description="Audit notes regarding evidence verification, filtered claims, and notes",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "decision_id": self.decision_id,
            "decision_summary": self.decision_summary,
            "status": self.status,
            "rationale": self.rationale.to_dict(),
            "supporting_arguments": [a.to_dict() for a in self.supporting_arguments],
            "opposing_arguments": [a.to_dict() for a in self.opposing_arguments],
            "rejected_alternatives": [a.to_dict() for a in self.rejected_alternatives],
            "trade_offs": [t.to_dict() for t in self.trade_offs],
            "consequences": [c.to_dict() for c in self.consequences],
            "evidence_comment_ids": self.evidence_comment_ids,
            "confidence": self.confidence,
            "extraction_notes": self.extraction_notes,
        }


class RationaleExtractionResult(BaseModel):
    """Top-level container for Module 5 rationale extraction output."""

    is_rationale_extracted: bool = Field(
        ...,
        description="Whether rationale was successfully extracted for any decision",
    )
    repository: str = Field(
        ...,
        description="Target GitHub repository in owner/repo format",
    )
    entity_number: int = Field(
        ...,
        description="GitHub Issue or Pull Request number",
    )
    resource_type: str = Field(
        ...,
        description="Resource type ('issue' or 'pull_request')",
    )
    source_url: str = Field(
        ...,
        description="Original GitHub permalink",
    )
    model_name: str = Field(
        ...,
        description="Model name used for rationale extraction",
    )
    decisions_evaluated: int = Field(
        default=0,
        description="Total number of detected candidate decisions evaluated",
    )
    rationales: List[ExtractedDecisionRationale] = Field(
        default_factory=list,
        description="List of verified rationale records",
    )
    total_evidence_citations: int = Field(
        default=0,
        description="Total number of unique comment evidence citations preserved",
    )
    processing_notes: List[str] = Field(
        default_factory=list,
        description="Diagnostic notes and validation audit trail",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert extraction result to JSON-serializable dictionary."""
        return {
            "is_rationale_extracted": self.is_rationale_extracted,
            "repository": self.repository,
            "entity_number": self.entity_number,
            "resource_type": self.resource_type,
            "source_url": self.source_url,
            "model_name": self.model_name,
            "decisions_evaluated": self.decisions_evaluated,
            "rationales": [r.to_dict() for r in self.rationales],
            "total_evidence_citations": self.total_evidence_citations,
            "processing_notes": self.processing_notes,
        }

