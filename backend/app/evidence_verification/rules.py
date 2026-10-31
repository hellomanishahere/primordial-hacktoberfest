"""Deterministic rule-based evidence verification and contradiction detection."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.preprocessing.schemas import CleanedDiscussionComment
from app.evidence_verification.schemas import (
    CommentProvenance,
    EvidenceType,
    VerificationStatus,
)

# Signals indicating explicit rejection or dismissal of an alternative approach
REJECTION_SIGNALS = [
    "reject", "rejected", "rejection", "declined", "won't work", "wont work",
    "cannot support", "can't support", "too slow", "discarded", "abandoned",
    "ruled out", "not viable", "decided against", "decided not to", "drawback",
    "instead of", "not recommended", "unsuitable", "sync blocking", "blocking",
    "overhead", "performance penalty", "incompatible", "dropped", "avoid"
]

# Signals indicating strong contradiction or objection to a claim or proposed solution
CONTRADICTION_SIGNALS = [
    "disagree", "object", "objection", "broken", "breaks", "does not work",
    "revert", "regression", "flawed", "cannot accept", "veto", "unsafe",
    "incorrect", "false", "misleading", "security issue", "vulnerability",
    "violates", "strongly oppose"
]

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "this", "that", "these", "those", "we", "they", "it",
    "which", "what", "as", "if", "not", "no", "can", "will", "would", "should"
}


def tokenize_statement(text: str) -> Set[str]:
    """Extract lowercase alphanumeric tokens excluding common English stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


def extract_provenance(
    comment: CleanedDiscussionComment,
    max_len: int = 300,
) -> CommentProvenance:
    """Builds CommentProvenance metadata from a CleanedDiscussionComment."""
    body_clean = comment.body.strip().replace("\n", " ")
    snippet = body_clean[:max_len] + ("..." if len(body_clean) > max_len else "")
    return CommentProvenance(
        comment_id=comment.id,
        author=comment.author,
        author_association=comment.author_association,
        created_at=comment.created_at,
        html_url=comment.html_url,
        body_snippet=snippet,
    )


def verify_claim_deterministically(
    claim_text: str,
    claim_type: str,
    cited_ids: List[str],
    comments_map: Dict[str, CleanedDiscussionComment],
    all_comments: List[CleanedDiscussionComment],
) -> Dict[str, Any]:
    """
    Performs rigorous deterministic evidence verification on an extracted claim.

    Rules applied:
    1. Cited ID existence: all IDs must exist in discussion comments map.
    2. Insufficient evidence marker: preserves explicit lack of evidence.
    3. Direct vs Inferred evidence: token overlap between claim and supporting comment bodies.
    4. Rejected alternative check: verifies that comments actually reject/dismiss the option,
       preventing mere mentions from being classified as rejected.
    5. Contradiction detection: scans comments for contradiction signals matching claim keywords.
    """
    notes: List[str] = []
    claim_tokens = tokenize_statement(claim_text)

    # 1. Check for explicit insufficient evidence indicators
    is_explicit_insufficient = any(
        marker in claim_text.lower()
        for marker in ("insufficient_evidence", "unknown", "none stated", "not specified", "unstated")
    )
    if is_explicit_insufficient:
        return {
            "status": VerificationStatus.INSUFFICIENT_EVIDENCE,
            "evidence_type": EvidenceType.NONE,
            "supporting_comment_ids": [],
            "contradicting_comment_ids": [],
            "supporting_provenance": [],
            "contradicting_provenance": [],
            "explanation": "Claim explicitly reflects that evidence was insufficient or not stated in the thread.",
            "confidence": 0.0,
            "notes": ["Explicit insufficient_evidence indicator preserved."],
        }

    # 2. Verify cited comment IDs exist
    valid_ids: List[str] = []
    missing_ids: List[str] = []
    supporting_comments: List[CleanedDiscussionComment] = []

    for cid in cited_ids:
        c = comments_map.get(cid)
        if c is not None:
            valid_ids.append(cid)
            supporting_comments.append(c)
        else:
            missing_ids.append(cid)

    if missing_ids:
        notes.append(f"Cited comment ID(s) {missing_ids} do not exist in discussion thread.")

    # 3. If no valid comments cited, claim is unsupported
    if not valid_ids:
        return {
            "status": VerificationStatus.UNSUPPORTED,
            "evidence_type": EvidenceType.NONE,
            "supporting_comment_ids": [],
            "contradicting_comment_ids": [],
            "supporting_provenance": [],
            "contradicting_provenance": [],
            "explanation": "Claim cites zero valid comments in the original discussion thread.",
            "confidence": 0.0,
            "notes": notes + ["Marked unsupported due to complete lack of authentic comment citations."],
        }

    # 4. Check token overlap with supporting comments to assess support strength
    max_overlap_ratio = 0.0
    combined_supporting_text = " ".join(c.body.lower() for c in supporting_comments)

    if claim_tokens:
        matched_tokens = {t for t in claim_tokens if t in combined_supporting_text}
        max_overlap_ratio = len(matched_tokens) / len(claim_tokens)
    else:
        max_overlap_ratio = 0.5

    # 5. Domain rule for rejected alternatives: Must have explicit rejection signal
    if claim_type == "rejected_alternative":
        has_rejection_signal = any(sig in combined_supporting_text for sig in REJECTION_SIGNALS)
        if not has_rejection_signal:
            notes.append(
                "Alternative was mentioned in cited comments, but no explicit rejection/dismissal keywords found in text."
            )
            # Reclassify as partially supported if mentioned, or unsupported if token match is poor
            provenance = [extract_provenance(c) for c in supporting_comments]
            return {
                "status": VerificationStatus.PARTIALLY_SUPPORTED if max_overlap_ratio >= 0.3 else VerificationStatus.UNSUPPORTED,
                "evidence_type": EvidenceType.INFERRED,
                "supporting_comment_ids": valid_ids,
                "contradicting_comment_ids": [],
                "supporting_provenance": provenance,
                "contradicting_provenance": [],
                "explanation": "Alternative was mentioned in discussion, but explicit dismissal or rejection justification is not established in cited comments.",
                "confidence": 0.45,
                "notes": notes,
            }

    # 6. Check for contradictory comments across discussion thread
    contradicting_ids: List[str] = []
    contradicting_provenance: List[CommentProvenance] = []

    for c in all_comments:
        c_body_lower = c.body.lower()
        # Look for combination of claim tokens + contradiction signals
        has_contra_signal = any(sig in c_body_lower for sig in CONTRADICTION_SIGNALS)
        if has_contra_signal:
            matched_contra_tokens = [t for t in claim_tokens if t in c_body_lower]
            if len(matched_contra_tokens) >= 2 and c.id not in valid_ids:
                contradicting_ids.append(c.id)
                contradicting_provenance.append(extract_provenance(c))

    if contradicting_ids:
        notes.append(f"Identified potential contradiction in comment(s) {contradicting_ids}.")

    supporting_provenance = [extract_provenance(c) for c in supporting_comments]

    # 7. Final status determination based on overlap and contradictions
    if contradicting_ids and max_overlap_ratio < 0.6:
        status = VerificationStatus.CONTRADICTED
        explanation = f"Claim is directly challenged or contradicted by comments {contradicting_ids}."
        confidence = 0.85
        evidence_type = EvidenceType.INFERRED
    elif missing_ids and valid_ids:
        status = VerificationStatus.PARTIALLY_SUPPORTED
        explanation = f"Claim supported by comments {valid_ids}, but cited comments {missing_ids} were invalid."
        confidence = round(max(0.4, min(0.75, max_overlap_ratio)), 2)
        evidence_type = EvidenceType.DIRECT if max_overlap_ratio >= 0.5 else EvidenceType.INFERRED
    elif max_overlap_ratio >= 0.5:
        status = VerificationStatus.VERIFIED
        evidence_type = EvidenceType.DIRECT
        explanation = f"Claim is directly corroborated by authentic comments {valid_ids}."
        confidence = round(max(0.7, min(0.98, 0.7 + (max_overlap_ratio * 0.28))), 2)
    elif max_overlap_ratio >= 0.25:
        status = VerificationStatus.PARTIALLY_SUPPORTED
        evidence_type = EvidenceType.INFERRED
        explanation = f"Claim is partially substantiated by comments {valid_ids} with moderate textual overlap."
        confidence = round(max(0.4, min(0.7, max_overlap_ratio)), 2)
    else:
        status = VerificationStatus.UNSUPPORTED
        evidence_type = EvidenceType.NONE
        explanation = f"Cited comments {valid_ids} show minimal textual or topical relevance to claim."
        confidence = 0.25

    return {
        "status": status,
        "evidence_type": evidence_type,
        "supporting_comment_ids": valid_ids,
        "contradicting_comment_ids": contradicting_ids,
        "supporting_provenance": supporting_provenance,
        "contradicting_provenance": contradicting_provenance,
        "explanation": explanation,
        "confidence": confidence,
        "notes": notes,
    }
