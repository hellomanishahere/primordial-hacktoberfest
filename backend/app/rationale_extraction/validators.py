"""Evidence validation, grounding verification, and anti-hallucination filters."""

from typing import List, Optional, Set, Tuple

from app.core.logging import get_logger
from app.rationale_extraction.schemas import (
    EvidenceStatus,
    ExtractedClaim,
    ExtractedDecisionRationale,
    RawDecisionRationale,
    RejectedAlternative,
)

logger = get_logger("rationale_extraction.validators")


def validate_claim_evidence(
    claim: ExtractedClaim,
    valid_comment_ids: Set[str],
    claim_type: str = "claim",
) -> Tuple[Optional[ExtractedClaim], List[str]]:
    """
    Validates that cited comment IDs exist in the authentic discussion.
    Strips hallucinated IDs and drops ungrounded claims.
    """
    notes: List[str] = []
    cited_ids = claim.supporting_comment_ids
    genuine_ids = [cid for cid in cited_ids if cid in valid_comment_ids]
    invalid_ids = [cid for cid in cited_ids if cid not in valid_comment_ids]

    if invalid_ids:
        notes.append(
            f"Filtered {len(invalid_ids)} invalid comment ID(s) {invalid_ids} from {claim_type} '{claim.statement[:40]}...'."
        )

    # Check if this claim explicitly signals lack of evidence
    is_explicit_insufficient = any(
        marker in claim.statement.lower()
        for marker in ("insufficient_evidence", "unknown", "none", "not specified", "unstated")
    )

    if not genuine_ids:
        if is_explicit_insufficient:
            # Preserve explicit insufficient evidence indicator
            claim.supporting_comment_ids = []
            claim.evidence_status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            claim.confidence = 0.0
            return claim, notes

        # Unsubstantiated claim with no valid citations -> drop
        notes.append(
            f"Dropped ungrounded {claim_type} '{claim.statement[:40]}...' because it cited no authentic comment IDs."
        )
        return None, notes

    claim.supporting_comment_ids = genuine_ids
    claim.evidence_status = EvidenceStatus.VERIFIED
    return claim, notes


def validate_rejected_alternative(
    alt: RejectedAlternative,
    valid_comment_ids: Set[str],
) -> Tuple[Optional[RejectedAlternative], List[str]]:
    """
    Validates evidence for rejected alternatives.
    Enforces that an alternative was actually discussed and dismissed in the thread.
    """
    notes: List[str] = []
    cited_ids = alt.supporting_comment_ids
    genuine_ids = [cid for cid in cited_ids if cid in valid_comment_ids]
    invalid_ids = [cid for cid in cited_ids if cid not in valid_comment_ids]

    if invalid_ids:
        notes.append(
            f"Filtered {len(invalid_ids)} invalid comment ID(s) {invalid_ids} from rejected alternative '{alt.statement[:40]}...'."
        )

    is_explicit_insufficient = any(
        marker in alt.statement.lower()
        for marker in ("insufficient_evidence", "unknown", "none", "not specified")
    )

    if not genuine_ids:
        if is_explicit_insufficient:
            alt.supporting_comment_ids = []
            alt.evidence_status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            alt.confidence = 0.0
            return alt, notes

        notes.append(
            f"Dropped rejected alternative '{alt.statement[:40]}...' because it cited no authentic comment IDs."
        )
        return None, notes

    alt.supporting_comment_ids = genuine_ids
    alt.evidence_status = EvidenceStatus.VERIFIED

    # Check rejection reason
    if not alt.rejection_reason or alt.rejection_reason.lower() in ("null", "none", "unknown"):
        alt.rejection_reason = "Unspecified in public thread"

    return alt, notes


def validate_decision_rationale(
    raw: RawDecisionRationale,
    candidate_status: str,
    valid_comment_ids: Set[str],
) -> ExtractedDecisionRationale:
    """
    Validates and grounds all extracted rationale components for a decision against authentic comments.
    """
    notes: List[str] = []
    if raw.extraction_notes:
        notes.append(f"Model Note: {raw.extraction_notes}")

    all_evidence_ids: Set[str] = set()

    # 1. Validate primary rationale
    validated_rationale, rat_notes = validate_claim_evidence(
        raw.rationale, valid_comment_ids, claim_type="primary rationale"
    )
    notes.extend(rat_notes)

    if validated_rationale is None:
        # If model's primary rationale lacked valid comment citations, mark as insufficient evidence
        notes.append(
            f"Primary rationale for decision '{raw.decision_id}' lacked valid evidence; marking as insufficient_evidence."
        )
        final_rationale = ExtractedClaim(
            statement=raw.rationale.statement or "insufficient_evidence",
            supporting_comment_ids=[],
            evidence_explanation="No authentic comment citations substantiate this rationale.",
            confidence=0.1,
            evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
        )
    else:
        final_rationale = validated_rationale
        all_evidence_ids.update(final_rationale.supporting_comment_ids)

    # 2. Validate supporting arguments
    validated_supporting: List[ExtractedClaim] = []
    for arg in raw.supporting_arguments:
        valid_arg, arg_notes = validate_claim_evidence(arg, valid_comment_ids, claim_type="supporting argument")
        notes.extend(arg_notes)
        if valid_arg:
            validated_supporting.append(valid_arg)
            all_evidence_ids.update(valid_arg.supporting_comment_ids)

    # 3. Validate opposing arguments (Never assume silence means disagreement)
    validated_opposing: List[ExtractedClaim] = []
    for arg in raw.opposing_arguments:
        valid_arg, arg_notes = validate_claim_evidence(arg, valid_comment_ids, claim_type="opposing argument")
        notes.extend(arg_notes)
        if valid_arg:
            validated_opposing.append(valid_arg)
            all_evidence_ids.update(valid_arg.supporting_comment_ids)

    # 4. Validate rejected alternatives (Do not assume idea was rejected without discussion evidence)
    validated_alternatives: List[RejectedAlternative] = []
    for alt in raw.rejected_alternatives:
        valid_alt, alt_notes = validate_rejected_alternative(alt, valid_comment_ids)
        notes.extend(alt_notes)
        if valid_alt:
            validated_alternatives.append(valid_alt)
            all_evidence_ids.update(valid_alt.supporting_comment_ids)

    # 5. Validate trade-offs
    validated_trade_offs: List[ExtractedClaim] = []
    for tf in raw.trade_offs:
        valid_tf, tf_notes = validate_claim_evidence(tf, valid_comment_ids, claim_type="trade-off")
        notes.extend(tf_notes)
        if valid_tf:
            validated_trade_offs.append(valid_tf)
            all_evidence_ids.update(valid_tf.supporting_comment_ids)

    # 6. Validate consequences
    validated_consequences: List[ExtractedClaim] = []
    for csq in raw.consequences:
        valid_csq, csq_notes = validate_claim_evidence(csq, valid_comment_ids, claim_type="consequence")
        notes.extend(csq_notes)
        if valid_csq:
            validated_consequences.append(valid_csq)
            all_evidence_ids.update(valid_csq.supporting_comment_ids)

    # 7. Confidence calibration
    if final_rationale.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE and not validated_supporting:
        overall_confidence = min(0.25, raw.confidence)
    else:
        scores = [final_rationale.confidence] + [a.confidence for a in validated_supporting + validated_opposing]
        overall_confidence = sum(scores) / len(scores) if scores else raw.confidence

    # 8. Sort evidence comment IDs deterministically
    sorted_evidence_ids = sorted(list(all_evidence_ids))

    return ExtractedDecisionRationale(
        decision_id=raw.decision_id,
        decision_summary=raw.decision_summary,
        status=candidate_status,
        rationale=final_rationale,
        supporting_arguments=validated_supporting,
        opposing_arguments=validated_opposing,
        rejected_alternatives=validated_alternatives,
        trade_offs=validated_trade_offs,
        consequences=validated_consequences,
        evidence_comment_ids=sorted_evidence_ids,
        confidence=round(overall_confidence, 2),
        extraction_notes=notes,
    )

