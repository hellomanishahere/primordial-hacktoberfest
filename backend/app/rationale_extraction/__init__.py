"""Rationale and argument extraction module for Primordial."""

from app.rationale_extraction.extractor import RationaleExtractor, extract_decision_rationale
from app.rationale_extraction.prompts import (
    RATIONALE_EXTRACTION_SYSTEM_PROMPT,
    build_rationale_correction_prompt,
    build_rationale_user_prompt,
)
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    ExtractedDecisionRationale,
    RationaleExtractionResult,
    RawDecisionRationale,
    RawRationaleExtractionResponse,
    RejectedAlternative,
)
from app.rationale_extraction.validators import (
    validate_claim_evidence,
    validate_decision_rationale,
    validate_rejected_alternative,
)

__all__ = [
    # Schemas
    "EvidenceStatus",
    "ExtractedClaim",
    "RejectedAlternative",
    "RawDecisionRationale",
    "RawRationaleExtractionResponse",
    "ExtractedDecisionRationale",
    "RationaleExtractionResult",
    # Prompts
    "RATIONALE_EXTRACTION_SYSTEM_PROMPT",
    "build_rationale_user_prompt",
    "build_rationale_correction_prompt",
    # Validator
    "validate_claim_evidence",
    "validate_rejected_alternative",
    "validate_decision_rationale",
    # Extractor
    "RationaleExtractor",
    "extract_decision_rationale",
]

