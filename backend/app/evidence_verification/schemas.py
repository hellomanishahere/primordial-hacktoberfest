"""Pydantic schemas and domain models for Evidence Verification (Module 7)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Rigorous verification status of an extracted claim against discussion evidence."""

    VERIFIED = "verified"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceType(str, Enum):
    """Categorization of evidence grounding quality."""

    DIRECT = "direct"
    INFERRED = "inferred"
    NONE = "none"


class CommentProvenance(BaseModel):
    """Authentic provenance metadata linking a claim back to an exact GitHub comment."""

    comment_id: str = Field(..., description="Unique GitHub comment identifier")
    author: str = Field(..., description="GitHub username of the comment author")
    author_association: str = Field(default="NONE", description="Role/association of author (e.g., MEMBER, CONTRIBUTOR)")
    created_at: datetime = Field(..., description="Original ISO timestamp of the comment")
    html_url: str = Field(..., description="Direct permalink to the comment on GitHub")
    body_snippet: str = Field(..., description="Substantive text excerpt relevant to the claim")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "author": self.author,
            "author_association": self.author_association,
            "created_at": self.created_at.isoformat(),
            "html_url": self.html_url,
            "body_snippet": self.body_snippet,
        }


class ClaimVerificationResult(BaseModel):
    """Verification outcome for an individual extracted claim, argument, alternative, or consequence."""

    claim_id: str = Field(..., description="Deterministic identifier for this claim")
    claim_type: str = Field(..., description="Category of claim (rationale, supporting_argument, opposing_argument, rejected_alternative, trade_off, consequence)")
    claim_text: str = Field(..., description="Verbatim text of the extracted claim")
    status: VerificationStatus = Field(..., description="Verification classification")
    evidence_type: EvidenceType = Field(default=EvidenceType.NONE, description="Direct textual match vs inferred rationale")
    supporting_comment_ids: List[str] = Field(default_factory=list, description="Validated comment IDs that provide positive evidence")
    contradicting_comment_ids: List[str] = Field(default_factory=list, description="Validated comment IDs containing conflicting or contradictory claims")
    supporting_provenance: List[CommentProvenance] = Field(default_factory=list, description="Provenance metadata for supporting comments")
    contradicting_provenance: List[CommentProvenance] = Field(default_factory=list, description="Provenance metadata for contradicting comments")
    explanation: str = Field(..., description="Detailed verification reasoning")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Verification confidence score between 0.0 and 1.0")
    verification_notes: List[str] = Field(default_factory=list, description="Deterministic and semantic audit findings")

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "claim_text": self.claim_text,
            "status": self.status.value,
            "evidence_type": self.evidence_type.value,
            "supporting_comment_ids": self.supporting_comment_ids,
            "contradicting_comment_ids": self.contradicting_comment_ids,
            "supporting_provenance": [p.to_dict() for p in self.supporting_provenance],
            "contradicting_provenance": [p.to_dict() for p in self.contradicting_provenance],
            "explanation": self.explanation,
            "confidence": self.confidence,
            "verification_notes": self.verification_notes,
        }


class DecisionVerificationResult(BaseModel):
    """Aggregate evidence verification result for an entire candidate engineering decision."""

    decision_id: str = Field(..., description="Identifier of the evaluated decision")
    decision_summary: str = Field(..., description="Declarative statement of the decision")
    candidate_status: str = Field(..., description="Lifecycle status from detection (e.g., accepted, rejected)")
    overall_verification_status: VerificationStatus = Field(..., description="Aggregate verification status for the decision")
    claim_verifications: List[ClaimVerificationResult] = Field(default_factory=list, description="Detailed verification of all individual claims")
    all_supporting_comment_ids: List[str] = Field(default_factory=list, description="Deduplicated list of all supporting comment IDs")
    all_contradicting_comment_ids: List[str] = Field(default_factory=list, description="Deduplicated list of all contradicting comment IDs")
    total_claims_evaluated: int = Field(default=0, description="Total number of claims checked")
    verified_claims_count: int = Field(default=0, description="Count of fully verified claims")
    partially_supported_count: int = Field(default=0, description="Count of partially supported claims")
    contradicted_count: int = Field(default=0, description="Count of contradicted claims")
    unsupported_count: int = Field(default=0, description="Count of unsupported claims")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Calibrated confidence of aggregate verification")
    verification_notes: List[str] = Field(default_factory=list, description="Decision-level audit notes")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_summary": self.decision_summary,
            "candidate_status": self.candidate_status,
            "overall_verification_status": self.overall_verification_status.value,
            "claim_verifications": [c.to_dict() for c in self.claim_verifications],
            "all_supporting_comment_ids": self.all_supporting_comment_ids,
            "all_contradicting_comment_ids": self.all_contradicting_comment_ids,
            "total_claims_evaluated": self.total_claims_evaluated,
            "verified_claims_count": self.verified_claims_count,
            "partially_supported_count": self.partially_supported_count,
            "contradicted_count": self.contradicted_count,
            "unsupported_count": self.unsupported_count,
            "confidence": self.confidence,
            "verification_notes": self.verification_notes,
        }


class EvidenceVerificationResult(BaseModel):
    """Top-level container for Module 7 Evidence Verification."""

    is_verification_completed: bool = Field(..., description="True if verification ran to completion")
    repository: str = Field(..., description="Target repository (owner/repo)")
    entity_number: int = Field(..., description="Discussion issue or PR number")
    resource_type: str = Field(..., description="issue or pull_request")
    source_url: str = Field(..., description="Original GitHub permalink")
    model_name: Optional[str] = Field(default=None, description="Model used for semantic verification, if any")
    decisions_evaluated: int = Field(default=0, description="Number of candidate decisions verified")
    verified_decisions: List[DecisionVerificationResult] = Field(default_factory=list, description="Verified decision records")
    total_claims_verified: int = Field(default=0, description="Sum of verified claims across all decisions")
    total_claims_contradicted: int = Field(default=0, description="Sum of contradicted claims across all decisions")
    total_claims_unsupported: int = Field(default=0, description="Sum of unsupported claims across all decisions")
    processing_notes: List[str] = Field(default_factory=list, description="High-level audit and processing log")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_verification_completed": self.is_verification_completed,
            "repository": self.repository,
            "entity_number": self.entity_number,
            "resource_type": self.resource_type,
            "source_url": self.source_url,
            "model_name": self.model_name,
            "decisions_evaluated": self.decisions_evaluated,
            "verified_decisions": [v.to_dict() for v in self.verified_decisions],
            "total_claims_verified": self.total_claims_verified,
            "total_claims_contradicted": self.total_claims_contradicted,
            "total_claims_unsupported": self.total_claims_unsupported,
            "processing_notes": self.processing_notes,
        }
