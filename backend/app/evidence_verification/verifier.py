"""Evidence verification pipeline and coordinator (Module 7)."""

from typing import Dict, List, Optional, Set

from app.core.config import settings
from app.core.logging import get_logger
from app.decision_detection.model_client import OllamaModelClient
from app.preprocessing.budgeter import DEFAULT_TOKEN_CEILING, format_discussion_transcript
from app.preprocessing.schemas import CleanedDiscussionComment, CleanedDiscussionThread
from app.rationale_extraction.schemas import (
    ExtractedClaim,
    ExtractedDecisionRationale,
    RationaleExtractionResult,
    RejectedAlternative,
)
from app.evidence_verification.rules import (
    verify_claim_deterministically,
)
from app.evidence_verification.schemas import (
    ClaimVerificationResult,
    DecisionVerificationResult,
    EvidenceVerificationResult,
    VerificationStatus,
)

logger = get_logger("evidence_verification.verifier")


class EvidenceVerifier:
    """Rigorous evidence verifier validating claims against source discussion comments."""

    def __init__(
        self,
        model_client: Optional[OllamaModelClient] = None,
        default_model: Optional[str] = None,
        enable_semantic_ai: bool = False,
    ) -> None:
        self.model_client = model_client or OllamaModelClient()
        self.default_model = default_model or settings.AI_MODEL_PRIMARY
        self.enable_semantic_ai = enable_semantic_ai

    async def verify(
        self,
        thread: CleanedDiscussionThread,
        rationale_result: Optional[RationaleExtractionResult] = None,
        model_name: Optional[str] = None,
        token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
    ) -> EvidenceVerificationResult:
        """
        Executes the evidence verification pipeline.

        1. Handles empty threads or discussions without decisions.
        2. Builds deterministic lookup map of genuine discussion comments.
        3. For each candidate decision in rationale_result:
           - Verifies primary rationale claim.
           - Verifies supporting arguments.
           - Verifies opposing arguments.
           - Verifies rejected alternatives (verifying rejection rationale).
           - Verifies trade-offs and consequences.
        4. Calculates aggregated verification metrics, status, and provenance.
        """
        active_model = model_name or self.default_model
        notes: List[str] = []

        # 1. Short-circuit on empty discussion
        if not thread.comments or thread.audit.is_empty:
            logger.info("Thread %s #%s is empty; skipping evidence verification.", thread.repository, thread.entity_number)
            return EvidenceVerificationResult(
                is_verification_completed=False,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_url=thread.html_url,
                model_name=active_model if self.enable_semantic_ai else None,
                decisions_evaluated=0,
                verified_decisions=[],
                total_claims_verified=0,
                total_claims_contradicted=0,
                total_claims_unsupported=0,
                processing_notes=["Discussion thread is empty. No evidence verification performed."],
            )

        # 2. Short-circuit if no decisions were detected or extracted
        if not rationale_result or not rationale_result.rationales or not rationale_result.is_rationale_extracted:
            logger.info("No extracted rationale records for %s #%s; skipping evidence verification.", thread.repository, thread.entity_number)
            return EvidenceVerificationResult(
                is_verification_completed=False,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_url=thread.html_url,
                model_name=active_model if self.enable_semantic_ai else None,
                decisions_evaluated=0,
                verified_decisions=[],
                total_claims_verified=0,
                total_claims_contradicted=0,
                total_claims_unsupported=0,
                processing_notes=["No extracted decisions/rationales to verify."],
            )

        # 3. Context budget check
        transcript, budgeted_thread = format_discussion_transcript(
            thread, token_ceiling=token_ceiling
        )
        if budgeted_thread.audit.was_truncated:
            notes.append("Discussion comments were truncated to fit token ceiling.")

        # Build comment lookup map
        comments_map: Dict[str, CleanedDiscussionComment] = {c.id: c for c in thread.comments}
        all_comments: List[CleanedDiscussionComment] = thread.comments

        verified_decisions: List[DecisionVerificationResult] = []
        total_claims_verified = 0
        total_claims_contradicted = 0
        total_claims_unsupported = 0

        # 4. Verify each decision's claims
        for decision in rationale_result.rationales:
            claim_results: List[ClaimVerificationResult] = []

            # 4a. Primary Rationale Claim
            rat_res = self._verify_single_claim(
                claim_id=f"{decision.decision_id}-rationale",
                claim_type="rationale",
                claim_text=decision.rationale.statement,
                cited_ids=decision.rationale.supporting_comment_ids,
                comments_map=comments_map,
                all_comments=all_comments,
            )
            claim_results.append(rat_res)

            # 4b. Supporting Arguments
            for i, arg in enumerate(decision.supporting_arguments):
                claim_res = self._verify_single_claim(
                    claim_id=f"{decision.decision_id}-supp-{i}",
                    claim_type="supporting_argument",
                    claim_text=arg.statement,
                    cited_ids=arg.supporting_comment_ids,
                    comments_map=comments_map,
                    all_comments=all_comments,
                )
                claim_results.append(claim_res)

            # 4c. Opposing Arguments
            for i, arg in enumerate(decision.opposing_arguments):
                claim_res = self._verify_single_claim(
                    claim_id=f"{decision.decision_id}-opp-{i}",
                    claim_type="opposing_argument",
                    claim_text=arg.statement,
                    cited_ids=arg.supporting_comment_ids,
                    comments_map=comments_map,
                    all_comments=all_comments,
                )
                claim_results.append(claim_res)

            # 4d. Rejected Alternatives
            for i, alt in enumerate(decision.rejected_alternatives):
                alt_text = f"{alt.statement} (Rejection reason: {alt.rejection_reason})"
                claim_res = self._verify_single_claim(
                    claim_id=f"{decision.decision_id}-alt-{i}",
                    claim_type="rejected_alternative",
                    claim_text=alt_text,
                    cited_ids=alt.supporting_comment_ids,
                    comments_map=comments_map,
                    all_comments=all_comments,
                )
                claim_results.append(claim_res)

            # 4e. Trade-offs
            for i, tf in enumerate(decision.trade_offs):
                claim_res = self._verify_single_claim(
                    claim_id=f"{decision.decision_id}-tradeoff-{i}",
                    claim_type="trade_off",
                    claim_text=tf.statement,
                    cited_ids=tf.supporting_comment_ids,
                    comments_map=comments_map,
                    all_comments=all_comments,
                )
                claim_results.append(claim_res)

            # 4f. Consequences
            for i, csq in enumerate(decision.consequences):
                claim_res = self._verify_single_claim(
                    claim_id=f"{decision.decision_id}-csq-{i}",
                    claim_type="consequence",
                    claim_text=csq.statement,
                    cited_ids=csq.supporting_comment_ids,
                    comments_map=comments_map,
                    all_comments=all_comments,
                )
                claim_results.append(claim_res)

            # Aggregate decision verification metrics
            all_supp_ids = sorted(list({
                cid for c in claim_results for cid in c.supporting_comment_ids
            }))
            all_contra_ids = sorted(list({
                cid for c in claim_results for cid in c.contradicting_comment_ids
            }))

            verified_count = sum(1 for c in claim_results if c.status == VerificationStatus.VERIFIED)
            partially_count = sum(1 for c in claim_results if c.status == VerificationStatus.PARTIALLY_SUPPORTED)
            contra_count = sum(1 for c in claim_results if c.status == VerificationStatus.CONTRADICTED)
            unsupported_count = sum(1 for c in claim_results if c.status == VerificationStatus.UNSUPPORTED)

            total_claims_verified += verified_count
            total_claims_contradicted += contra_count
            total_claims_unsupported += unsupported_count

            # Overall status calculation
            if contra_count > 0:
                overall_status = VerificationStatus.CONTRADICTED
            elif unsupported_count == len(claim_results):
                overall_status = VerificationStatus.UNSUPPORTED
            elif verified_count == len(claim_results):
                overall_status = VerificationStatus.VERIFIED
            elif (verified_count + partially_count) > 0:
                overall_status = VerificationStatus.PARTIALLY_SUPPORTED
            else:
                overall_status = VerificationStatus.INSUFFICIENT_EVIDENCE

            avg_confidence = (
                sum(c.confidence for c in claim_results) / len(claim_results)
                if claim_results
                else 0.0
            )

            decision_notes: List[str] = []
            if contra_count > 0:
                decision_notes.append(f"Decision contains {contra_count} contradicted claim(s).")
            if unsupported_count > 0:
                decision_notes.append(f"Decision contains {unsupported_count} unsupported claim(s).")

            verified_decisions.append(
                DecisionVerificationResult(
                    decision_id=decision.decision_id,
                    decision_summary=decision.decision_summary,
                    candidate_status=decision.status,
                    overall_verification_status=overall_status,
                    claim_verifications=claim_results,
                    all_supporting_comment_ids=all_supp_ids,
                    all_contradicting_comment_ids=all_contra_ids,
                    total_claims_evaluated=len(claim_results),
                    verified_claims_count=verified_count,
                    partially_supported_count=partially_count,
                    contradicted_count=contra_count,
                    unsupported_count=unsupported_count,
                    confidence=round(avg_confidence, 2),
                    verification_notes=decision_notes,
                )
            )

        notes.append(
            f"Evidence verification completed: {len(verified_decisions)} decision(s) evaluated, "
            f"{total_claims_verified} claim(s) verified, {total_claims_contradicted} contradicted, "
            f"{total_claims_unsupported} unsupported."
        )

        return EvidenceVerificationResult(
            is_verification_completed=True,
            repository=thread.repository,
            entity_number=thread.entity_number,
            resource_type=thread.resource_type,
            source_url=thread.html_url,
            model_name=active_model if self.enable_semantic_ai else None,
            decisions_evaluated=len(verified_decisions),
            verified_decisions=verified_decisions,
            total_claims_verified=total_claims_verified,
            total_claims_contradicted=total_claims_contradicted,
            total_claims_unsupported=total_claims_unsupported,
            processing_notes=notes,
        )

    def _verify_single_claim(
        self,
        claim_id: str,
        claim_type: str,
        claim_text: str,
        cited_ids: List[str],
        comments_map: Dict[str, CleanedDiscussionComment],
        all_comments: List[CleanedDiscussionComment],
    ) -> ClaimVerificationResult:
        """Executes verification on a single claim using deterministic rules."""
        det_result = verify_claim_deterministically(
            claim_text=claim_text,
            claim_type=claim_type,
            cited_ids=cited_ids,
            comments_map=comments_map,
            all_comments=all_comments,
        )

        return ClaimVerificationResult(
            claim_id=claim_id,
            claim_type=claim_type,
            claim_text=claim_text,
            status=det_result["status"],
            evidence_type=det_result["evidence_type"],
            supporting_comment_ids=det_result["supporting_comment_ids"],
            contradicting_comment_ids=det_result["contradicting_comment_ids"],
            supporting_provenance=det_result["supporting_provenance"],
            contradicting_provenance=det_result["contradicting_provenance"],
            explanation=det_result["explanation"],
            confidence=det_result["confidence"],
            verification_notes=det_result["notes"],
        )


async def verify_evidence(
    thread: CleanedDiscussionThread,
    rationale_result: Optional[RationaleExtractionResult] = None,
    model_name: Optional[str] = None,
    model_client: Optional[OllamaModelClient] = None,
    token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
    enable_semantic_ai: bool = False,
) -> EvidenceVerificationResult:
    """Functional convenience entrypoint for evidence verification."""
    verifier = EvidenceVerifier(
        model_client=model_client,
        default_model=model_name,
        enable_semantic_ai=enable_semantic_ai,
    )
    return await verifier.verify(
        thread=thread,
        rationale_result=rationale_result,
        model_name=model_name,
        token_ceiling=token_ceiling,
    )

