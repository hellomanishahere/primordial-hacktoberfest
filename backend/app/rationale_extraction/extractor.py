"""Core rationale and argument extraction coordinator and pipeline."""

import json
from typing import List, Optional, Set
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import AIModelResponseException, SchemaValidationException
from app.core.logging import get_logger
from app.decision_detection.model_client import OllamaModelClient
from app.decision_detection.schemas import CandidateDecision, DecisionDetectionResult
from app.preprocessing.budgeter import DEFAULT_TOKEN_CEILING, format_discussion_transcript
from app.preprocessing.schemas import CleanedDiscussionThread
from app.rationale_extraction.prompts import (
    RATIONALE_EXTRACTION_SYSTEM_PROMPT,
    build_rationale_correction_prompt,
    build_rationale_user_prompt,
)
from app.rationale_extraction.schemas import (
    ExtractedDecisionRationale,
    RationaleExtractionResult,
    RawRationaleExtractionResponse,
)
from app.rationale_extraction.validators import validate_decision_rationale

logger = get_logger("rationale_extraction.extractor")


class RationaleExtractor:
    """Extracts structured technical rationale, arguments, trade-offs, and alternatives."""

    def __init__(
        self,
        model_client: Optional[OllamaModelClient] = None,
        default_model: Optional[str] = None,
        max_retries: int = 1,
    ) -> None:
        self.model_client = model_client or OllamaModelClient()
        self.default_model = default_model or settings.AI_MODEL_PRIMARY
        self.max_retries = max_retries

    async def extract(
        self,
        thread: CleanedDiscussionThread,
        detection_result: Optional[DecisionDetectionResult] = None,
        model_name: Optional[str] = None,
        token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
    ) -> RationaleExtractionResult:
        """
        Executes the rationale extraction workflow on detected decisions.

        1. Short-circuits on empty threads or when no decisions were detected.
        2. Formats and budgets the discussion transcript.
        3. Prompts the LLM with detected decisions and structured JSON schema constraint.
        4. Validates model output with Pydantic and executes controlled retry if malformed.
        5. Validates evidence citations against genuine thread comments.
        6. Assembles RationaleExtractionResult with verified citations.
        """
        active_model = model_name or self.default_model
        notes: List[str] = []

        # 1. Short-circuit on empty discussion
        if not thread.comments or thread.audit.is_empty:
            logger.info("Thread %s #%s is empty; skipping rationale extraction.", thread.repository, thread.entity_number)
            return RationaleExtractionResult(
                is_rationale_extracted=False,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_url=thread.html_url,
                model_name=active_model,
                decisions_evaluated=0,
                rationales=[],
                total_evidence_citations=0,
                processing_notes=["Discussion thread is empty. No rationale extraction performed."],
            )

        # 2. Short-circuit if no decisions were detected
        candidate_decisions = detection_result.decisions if detection_result and detection_result.is_decision_detected else []
        if not candidate_decisions:
            logger.info("No decisions detected for %s #%s; skipping rationale extraction.", thread.repository, thread.entity_number)
            return RationaleExtractionResult(
                is_rationale_extracted=False,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_url=thread.html_url,
                model_name=active_model,
                decisions_evaluated=0,
                rationales=[],
                total_evidence_citations=0,
                processing_notes=["No candidate decisions detected in discussion. Skipping rationale extraction."],
            )

        # 3. Context budgeting and transcript compilation
        transcript, budgeted_thread = format_discussion_transcript(
            thread, token_ceiling=token_ceiling
        )
        if budgeted_thread.audit.was_truncated:
            notes.append("Discussion context exceeded token ceiling and was truncated to fit model budget.")

        valid_comment_ids: Set[str] = {c.id for c in budgeted_thread.comments}

        # 4. Build prompt and schema constraint
        user_prompt = build_rationale_user_prompt(
            transcript=transcript,
            decisions=candidate_decisions,
            repository=thread.repository,
            entity_number=thread.entity_number,
            resource_type=thread.resource_type,
            title=thread.title,
        )
        schema_constraint = RawRationaleExtractionResponse.model_json_schema()

        # 5. Model execution with controlled retry
        parsed_response: Optional[RawRationaleExtractionResponse] = None
        last_error_str = ""
        last_raw_content = ""

        for attempt in range(self.max_retries + 1):
            is_retry = attempt > 0
            current_prompt = (
                build_rationale_correction_prompt(last_error_str, last_raw_content)
                if is_retry
                else user_prompt
            )

            try:
                raw_json = await self.model_client.generate_chat(
                    prompt=current_prompt,
                    system_prompt=RATIONALE_EXTRACTION_SYSTEM_PROMPT,
                    model=active_model,
                    format_schema=schema_constraint,
                )
            except AIModelResponseException as exc:
                last_error_str = exc.message
                last_raw_content = str(exc.details.get("raw_content", ""))
                notes.append(f"Rationale model attempt {attempt + 1} failed: {exc.message}")
                if attempt >= self.max_retries:
                    notes.append("Retry exhausted: model failed to return valid JSON.")
                    raise
                continue

            try:
                parsed_response = RawRationaleExtractionResponse.model_validate(raw_json)
                if is_retry:
                    notes.append("Successfully recovered valid rationale response schema after 1 correction retry.")
                break
            except ValidationError as exc:
                err_details = "; ".join(f"{e['loc']}: {e['msg']}" for e in exc.errors())
                last_error_str = err_details
                last_raw_content = json.dumps(raw_json)
                notes.append(f"Rationale model attempt {attempt + 1} failed schema validation: {err_details}")
                if attempt >= self.max_retries:
                    notes.append(f"Retry exhausted: rationale schema validation failed again: {err_details}")
                    raise SchemaValidationException(
                        message="AI rationale extraction output failed schema validation",
                        details={"errors": exc.errors(), "raw_response": raw_json, "retry_exhausted": True},
                    ) from exc

        if parsed_response is None:
            raise SchemaValidationException(
                message="AI rationale extraction failed to obtain valid schema response",
                details={"last_error": last_error_str},
            )

        if parsed_response.deliberation_summary:
            notes.append(f"Deliberation Summary: {parsed_response.deliberation_summary}")

        # 6. Validate evidence and ground each extracted decision rationale
        candidate_map = {d.decision_id: d for d in candidate_decisions}
        validated_rationales: List[ExtractedDecisionRationale] = []

        for raw_rat in parsed_response.rationales:
            matched_candidate = candidate_map.get(raw_rat.decision_id)
            candidate_status = matched_candidate.status.value if matched_candidate else "accepted"

            grounded_rationale = validate_decision_rationale(
                raw=raw_rat,
                candidate_status=candidate_status,
                valid_comment_ids=valid_comment_ids,
            )
            validated_rationales.append(grounded_rationale)

        total_evidence_citations = len({
            cid for r in validated_rationales for cid in r.evidence_comment_ids
        })

        is_extracted = len(validated_rationales) > 0 and parsed_response.is_rationale_extracted

        return RationaleExtractionResult(
            is_rationale_extracted=is_extracted,
            repository=thread.repository,
            entity_number=thread.entity_number,
            resource_type=thread.resource_type,
            source_url=thread.html_url,
            model_name=active_model,
            decisions_evaluated=len(candidate_decisions),
            rationales=validated_rationales,
            total_evidence_citations=total_evidence_citations,
            processing_notes=notes,
        )


async def extract_decision_rationale(
    thread: CleanedDiscussionThread,
    detection_result: Optional[DecisionDetectionResult] = None,
    model_name: Optional[str] = None,
    model_client: Optional[OllamaModelClient] = None,
    token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
    max_retries: int = 1,
) -> RationaleExtractionResult:
    """Functional convenience entrypoint for rationale extraction."""
    extractor = RationaleExtractor(
        model_client=model_client,
        default_model=model_name,
        max_retries=max_retries,
    )
    return await extractor.extract(
        thread=thread,
        detection_result=detection_result,
        model_name=model_name,
        token_ceiling=token_ceiling,
    )

