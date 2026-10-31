"""Core decision detection coordinator and evidence grounding validator."""

from typing import List, Optional, Set
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import SchemaValidationException
from app.core.logging import get_logger
from app.decision_detection.model_client import OllamaModelClient
from app.decision_detection.prompts import (
    DECISION_DETECTION_SYSTEM_PROMPT,
    build_detection_user_prompt,
)
from app.decision_detection.schemas import (
    CandidateDecision,
    DecisionDetectionResult,
    RawModelDecisionDetectionResponse,
)
from app.preprocessing.budgeter import DEFAULT_TOKEN_CEILING, format_discussion_transcript
from app.preprocessing.schemas import CleanedDiscussionThread

logger = get_logger("decision_detection.detector")


class DecisionDetector:
    """Detects technical and architectural decisions from preprocessed GitHub discussions."""

    def __init__(
        self,
        model_client: Optional[OllamaModelClient] = None,
        default_model: Optional[str] = None,
    ) -> None:
        self.model_client = model_client or OllamaModelClient()
        self.default_model = default_model or settings.AI_MODEL_PRIMARY

    async def detect(
        self,
        thread: CleanedDiscussionThread,
        model_name: Optional[str] = None,
        token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
    ) -> DecisionDetectionResult:
        """
        Runs the decision detection pipeline on a CleanedDiscussionThread.

        1. Handles empty threads immediately without calling the AI model.
        2. Formats and budgets the discussion transcript.
        3. Prompts the model for structured decision extraction.
        4. Validates model output using Pydantic schemas.
        5. Enforces Level 1 evidence verification by ensuring all cited comment IDs exist.
        6. Drops unsupported or hallucinated candidates.
        """
        active_model = model_name or self.default_model
        notes: List[str] = []

        # 1. Short-circuit on empty discussion
        if not thread.comments or thread.audit.is_empty:
            logger.info(
                "Thread %s #%s is empty; skipping AI detection.",
                thread.repository,
                thread.entity_number,
            )
            return DecisionDetectionResult(
                is_decision_detected=False,
                decisions=[],
                total_decisions=0,
                model_name=active_model,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_url=thread.html_url,
                processing_notes=["Discussion thread is empty. No decisions detected."],
            )

        # 2. Context budgeting and transcript compilation
        transcript, budgeted_thread = format_discussion_transcript(
            thread, token_ceiling=token_ceiling
        )
        if budgeted_thread.audit.was_truncated:
            notes.append(
                "Discussion context exceeded token ceiling and was truncated to fit model budget."
            )

        # Record available valid comment IDs for grounding verification
        valid_comment_ids: Set[str] = {c.id for c in budgeted_thread.comments}

        # 3. Build prompts
        user_prompt = build_detection_user_prompt(
            transcript=transcript,
            repository=thread.repository,
            entity_number=thread.entity_number,
            resource_type=thread.resource_type,
            title=thread.title,
        )

        # 4. Invoke Model
        raw_json = await self.model_client.generate_chat(
            prompt=user_prompt,
            system_prompt=DECISION_DETECTION_SYSTEM_PROMPT,
            model=active_model,
        )

        # 5. Validate model output with Pydantic
        try:
            parsed_response = RawModelDecisionDetectionResponse.model_validate(raw_json)
        except ValidationError as exc:
            logger.error("Raw model response failed schema validation: %s", exc)
            raise SchemaValidationException(
                message="AI decision detection output failed schema validation",
                details={"errors": exc.errors(), "raw_response": raw_json},
            ) from exc

        if parsed_response.reasoning:
            notes.append(f"Model Deliberation Reasoning: {parsed_response.reasoning}")

        # 6. Verify evidence links and construct CandidateDecisions
        validated_decisions: List[CandidateDecision] = []
        for idx, raw_candidate in enumerate(parsed_response.decisions):
            # Check comment citations
            cited_ids = raw_candidate.supporting_comment_ids
            genuine_ids = [cid for cid in cited_ids if cid in valid_comment_ids]
            invalid_ids = [cid for cid in cited_ids if cid not in valid_comment_ids]

            if invalid_ids:
                notes.append(
                    f"Filtered {len(invalid_ids)} hallucinated comment ID(s) {invalid_ids} "
                    f"from candidate '{raw_candidate.decision_statement[:40]}...'."
                )

            # If no genuine IDs remain, discard this ungrounded candidate
            if not genuine_ids:
                logger.warning(
                    "Dropping ungrounded candidate decision '%s' with no valid comment IDs.",
                    raw_candidate.decision_statement[:60],
                )
                notes.append(
                    f"Dropped candidate decision '{raw_candidate.decision_statement[:50]}...' "
                    "because it lacked valid supporting comment IDs from the discussion."
                )
                continue

            decision_id = f"dec-{thread.entity_number}-{len(validated_decisions) + 1}"
            candidate = CandidateDecision(
                decision_id=decision_id,
                decision_statement=raw_candidate.decision_statement,
                status=raw_candidate.status,
                confidence=raw_candidate.confidence,
                supporting_comment_ids=genuine_ids,
                repository=thread.repository,
                entity_number=thread.entity_number,
                resource_type=thread.resource_type,
                source_title=thread.title,
                model_name=active_model,
            )
            validated_decisions.append(candidate)

        is_detected = parsed_response.is_decision_detected and len(validated_decisions) > 0

        return DecisionDetectionResult(
            is_decision_detected=is_detected,
            decisions=validated_decisions,
            total_decisions=len(validated_decisions),
            model_name=active_model,
            repository=thread.repository,
            entity_number=thread.entity_number,
            resource_type=thread.resource_type,
            source_url=thread.html_url,
            processing_notes=notes,
        )


async def detect_decisions(
    thread: CleanedDiscussionThread,
    model_name: Optional[str] = None,
    model_client: Optional[OllamaModelClient] = None,
    token_ceiling: Optional[int] = DEFAULT_TOKEN_CEILING,
) -> DecisionDetectionResult:
    """Functional convenience entrypoint for decision detection."""
    detector = DecisionDetector(model_client=model_client, default_model=model_name)
    return await detector.detect(thread, model_name=model_name, token_ceiling=token_ceiling)
