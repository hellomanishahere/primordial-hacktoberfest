"""AI Decision Detection module for Primordial."""

from app.decision_detection.detector import DecisionDetector, detect_decisions
from app.decision_detection.model_client import OllamaModelClient
from app.decision_detection.prompts import (
    DECISION_DETECTION_SYSTEM_PROMPT,
    build_detection_user_prompt,
)
from app.decision_detection.schemas import (
    CandidateDecision,
    CandidateDecisionStatus,
    DecisionDetectionResult,
    RawModelDecision,
    RawModelDecisionDetectionResponse,
)

__all__ = [
    # Schemas
    "CandidateDecisionStatus",
    "CandidateDecision",
    "DecisionDetectionResult",
    "RawModelDecision",
    "RawModelDecisionDetectionResponse",
    # Prompts
    "DECISION_DETECTION_SYSTEM_PROMPT",
    "build_detection_user_prompt",
    # Client & Detector
    "OllamaModelClient",
    "DecisionDetector",
    "detect_decisions",
]
