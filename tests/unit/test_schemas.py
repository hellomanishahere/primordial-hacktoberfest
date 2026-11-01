"""Unit tests for Pydantic schemas and domain contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.domain.schemas import (
    ClassificationResult,
    ComponentHealth,
    DecisionPayload,
    DecisionStatus,
    HealthResponse,
    OptionStatus,
)


def test_health_response_schema():
    health = HealthResponse(
        status="ok",
        app="Primordial",
        version="0.1.0",
        environment="test",
        database=ComponentHealth(status="ok", details="SQLite connected"),
        ollama=ComponentHealth(status="available", details="Ollama online", url="http://localhost:11434"),
    )
    data = health.model_dump()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "ok"
    assert data["ollama"]["url"] == "http://localhost:11434"


def test_classification_result_validation():
    result = ClassificationResult(
        is_decision=True,
        confidence_score=0.95,
        reasoning="Consensus reached to adopt library.",
    )
    assert result.is_decision is True
    assert result.confidence_score == 0.95

    # Test confidence score boundary validation
    with pytest.raises(ValidationError):
        ClassificationResult(
            is_decision=True,
            confidence_score=1.5,  # Out of [0.0, 1.0]
            reasoning="Invalid score",
        )


def test_decision_payload_schema():
    payload = DecisionPayload(
        title="Adopt Undici for Fetch API",
        status=DecisionStatus.ACCEPTED,
        context_and_problem="Standard fetch API needed in core.",
        decision_drivers=["Spec compliance", "Performance"],
    )
    assert payload.status == DecisionStatus.ACCEPTED
    assert payload.chosen_option is None
    assert payload.considered_options == []
    assert payload.consequences.positive == []
    assert payload.consequences.negative == []

