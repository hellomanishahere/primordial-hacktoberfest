"""Evidence Verification Module (Module 7)."""

from app.evidence_verification.schemas import (
    ClaimVerificationResult,
    CommentProvenance,
    DecisionVerificationResult,
    EvidenceType,
    EvidenceVerificationResult,
    VerificationStatus,
)
from app.evidence_verification.verifier import (
    EvidenceVerifier,
    verify_evidence,
)
from app.evidence_verification.rules import (
    extract_provenance,
    verify_claim_deterministically,
)

__all__ = [
    "VerificationStatus",
    "EvidenceType",
    "CommentProvenance",
    "ClaimVerificationResult",
    "DecisionVerificationResult",
    "EvidenceVerificationResult",
    "EvidenceVerifier",
    "verify_evidence",
    "extract_provenance",
    "verify_claim_deterministically",
]

