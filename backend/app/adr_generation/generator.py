"""ADR document compilation and generation pipeline (Module 8)."""

from typing import Any, Dict, List, Optional
from app.core.logging import get_logger
from app.preprocessing.schemas import CleanedDiscussionComment, CleanedDiscussionThread
from app.rationale_extraction.schemas import RationaleExtractionResult
from app.evidence_verification.schemas import (
    ClaimVerificationResult,
    DecisionVerificationResult,
    EvidenceVerificationResult,
    VerificationStatus,
)
from app.adr_generation.schemas import (
    ADRAlternative,
    ADRDocument,
    ADREvidenceRef,
    ADRGenerationResult,
    ADRStatus,
)

logger = get_logger("adr_generation.generator")


class ADRGenerator:
    """Compiles structured Architecture Decision Records from verified evidence."""

    def generate(
        self,
        thread: CleanedDiscussionThread,
        verification_result: EvidenceVerificationResult,
        rationale_result: Optional[RationaleExtractionResult] = None,
    ) -> ADRGenerationResult:
        """
        Generates ADR documents for each verified decision.
        """
        notes: List[str] = []

        if not verification_result.verified_decisions:
            logger.info("No verified decisions available for %s #%s; skipping ADR generation.", thread.repository, thread.entity_number)
            return ADRGenerationResult(
                total_adrs=0,
                adrs=[],
                repository=thread.repository,
                entity_number=thread.entity_number,
                source_url=thread.html_url,
                processing_notes=["No verified decisions available to compile ADRs."],
            )

        comments_map: Dict[str, CleanedDiscussionComment] = {c.id: c for c in thread.comments}
        compiled_adrs: List[ADRDocument] = []

        # Find matching rationale records if available
        rationale_map = {}
        if rationale_result and rationale_result.rationales:
            rationale_map = {r.decision_id: r for r in rationale_result.rationales}

        for idx, vdec in enumerate(verification_result.verified_decisions, start=1):
            adr_doc = self._compile_single_adr(
                idx=idx,
                vdec=vdec,
                thread=thread,
                comments_map=comments_map,
                raw_rationale=rationale_map.get(vdec.decision_id),
            )
            compiled_adrs.append(adr_doc)

        notes.append(f"Successfully generated {len(compiled_adrs)} ADR document(s).")

        return ADRGenerationResult(
            total_adrs=len(compiled_adrs),
            adrs=compiled_adrs,
            repository=thread.repository,
            entity_number=thread.entity_number,
            source_url=thread.html_url,
            processing_notes=notes,
        )

    def _compile_single_adr(
        self,
        idx: int,
        vdec: DecisionVerificationResult,
        thread: CleanedDiscussionThread,
        comments_map: Dict[str, CleanedDiscussionComment],
        raw_rationale: Optional[Any] = None,
    ) -> ADRDocument:
        """Compiles a single verified decision into an ADRDocument."""
        # 1. Assign stable ADR ID
        adr_id = f"ADR-{thread.entity_number}-{idx:02d}"
        title = vdec.decision_summary

        # 2. Map status accurately
        status_raw = vdec.candidate_status.lower()
        if status_raw in ("accepted", "approved"):
            status = ADRStatus.ACCEPTED
        elif status_raw in ("rejected", "declined", "abandoned"):
            status = ADRStatus.REJECTED
        elif status_raw in ("proposed", "open"):
            status = ADRStatus.PROPOSED
        elif status_raw in ("deferred", "postponed"):
            status = ADRStatus.DEFERRED
        else:
            status = ADRStatus.UNCLEAR

        # 3. Context & problem statement
        date_str = thread.created_at.strftime("%Y-%m-%d")
        context = thread.body.strip() if thread.body else "Not established in discussion."
        problem_statement = thread.title if thread.title else "Not established in discussion."

        # 4. Extract claims by type
        decision_drivers: List[str] = []
        positive_consequences: List[str] = []
        negative_consequences: List[str] = []
        trade_offs: List[str] = []
        considered_alternatives: List[ADRAlternative] = []

        supporting_refs: List[ADREvidenceRef] = []
        contradictory_refs: List[ADREvidenceRef] = []

        seen_supp_ids = set()
        seen_contra_ids = set()

        for claim in vdec.claim_verifications:
            # Map evidence references
            for prov in claim.supporting_provenance:
                if prov.comment_id not in seen_supp_ids:
                    seen_supp_ids.add(prov.comment_id)
                    supporting_refs.append(
                        ADREvidenceRef(
                            comment_id=prov.comment_id,
                            author=prov.author,
                            created_at=prov.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            html_url=prov.html_url,
                            quote_snippet=prov.body_snippet,
                            verification_status=claim.status.value,
                        )
                    )

            for prov in claim.contradicting_provenance:
                if prov.comment_id not in seen_contra_ids:
                    seen_contra_ids.add(prov.comment_id)
                    contradictory_refs.append(
                        ADREvidenceRef(
                            comment_id=prov.comment_id,
                            author=prov.author,
                            created_at=prov.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            html_url=prov.html_url,
                            quote_snippet=prov.body_snippet,
                            verification_status="contradicted",
                        )
                    )

            # Categorize claims into ADR sections
            label = f"[{claim.status.value.upper()}] {claim.claim_text}"

            if claim.claim_type in ("rationale", "supporting_argument"):
                decision_drivers.append(label)
            elif claim.claim_type == "trade_off":
                trade_offs.append(label)
            elif claim.claim_type == "consequence":
                positive_consequences.append(label)
            elif claim.claim_type == "opposing_argument":
                negative_consequences.append(label)
            elif claim.claim_type == "rejected_alternative":
                # Parse rejection reason
                alt_refs = [
                    ADREvidenceRef(
                        comment_id=p.comment_id,
                        author=p.author,
                        created_at=p.created_at.strftime("%Y-%m-%d"),
                        html_url=p.html_url,
                        quote_snippet=p.body_snippet,
                        verification_status=claim.status.value,
                    )
                    for p in claim.supporting_provenance
                ]
                considered_alternatives.append(
                    ADRAlternative(
                        title=claim.claim_text,
                        rejection_reason=claim.explanation or "Not established in discussion.",
                        evidence_refs=alt_refs,
                        verification_status=claim.status.value,
                    )
                )

        file_slug = ADRDocument.generate_slug(adr_id, title)

        return ADRDocument(
            adr_id=adr_id,
            title=title,
            status=status,
            date=date_str,
            context=context,
            problem_statement=problem_statement,
            decision=vdec.decision_summary,
            decision_drivers=decision_drivers,
            considered_alternatives=considered_alternatives,
            consequences_positive=positive_consequences,
            consequences_negative=negative_consequences,
            trade_offs=trade_offs,
            supporting_evidence=supporting_refs,
            contradictory_evidence=contradictory_refs,
            github_discussion_url=thread.html_url,
            repository=thread.repository,
            entity_number=thread.entity_number,
            file_slug=file_slug,
        )


def generate_adrs(
    thread: CleanedDiscussionThread,
    verification_result: EvidenceVerificationResult,
    rationale_result: Optional[RationaleExtractionResult] = None,
) -> ADRGenerationResult:
    """Functional convenience entrypoint for ADR compilation."""
    generator = ADRGenerator()
    return generator.generate(
        thread=thread,
        verification_result=verification_result,
        rationale_result=rationale_result,
    )
