"""FastAPI endpoint for running the end-to-end extraction pipeline (Modules 2-9)."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import (
    AIModelResponseException,
    AIModelTimeoutException,
    AIServiceUnavailableException,
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    InvalidGitHubURLException,
    PrimordialException,
    SchemaValidationException,
)
from app.core.logging import get_logger
from app.decision_detection.detector import detect_decisions
from app.evidence_verification.verifier import verify_evidence
from app.github.client import GitHubClient
from app.github.normalizer import normalize_github_discussion
from app.github.parser import parse_github_url
from app.preprocessing.cleaner import clean_discussion_thread
from app.rationale_extraction.extractor import extract_decision_rationale
from app.adr_generation.generator import generate_adrs
from app.storage.database import init_db
from app.storage.repository import StorageRepository

logger = get_logger("api.extract")
router = APIRouter()


class ExtractRequest(BaseModel):
    """Payload to trigger end-to-end Primordial knowledge extraction."""

    url: str = Field(..., description="Public GitHub Issue or Pull Request URL")
    model: Optional[str] = Field(default=None, description="Ollama AI model to execute")
    max_tokens: int = Field(default=12000, ge=1000, le=32000, description="Token ceiling")


@router.post(
    "/extract",
    status_code=status.HTTP_200_OK,
    summary="Execute Complete Pipeline & Recover Architectural Decisions",
    description="Fetches GitHub discussion, cleans noise, detects decisions, extracts rationale, verifies evidence, compiles ADRs, and persists to knowledge store.",
)
async def extract_discussion(payload: ExtractRequest) -> Dict[str, Any]:
    """Runs complete Primordial decision intelligence pipeline synchronously."""
    try:
        target = parse_github_url(payload.url)
    except InvalidGitHubURLException as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except GitHubResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except PrimordialException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    cleaned_thread = clean_discussion_thread(canonical_thread)
    active_model = payload.model or settings.AI_MODEL_PRIMARY

    # Step 1: Decision Detection
    try:
        detection_result = await detect_decisions(
            cleaned_thread, model_name=active_model, token_ceiling=payload.max_tokens
        )
    except AIServiceUnavailableException as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AIModelTimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=exc.message) from exc
    except (AIModelResponseException, SchemaValidationException) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc

    # Step 2: Rationale Extraction
    try:
        extraction_result = await extract_decision_rationale(
            thread=cleaned_thread,
            detection_result=detection_result,
            model_name=active_model,
            token_ceiling=payload.max_tokens,
        )
    except AIServiceUnavailableException as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except AIModelTimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=exc.message) from exc
    except (AIModelResponseException, SchemaValidationException) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc

    # Step 3: Evidence Verification
    verification_result = await verify_evidence(
        thread=cleaned_thread,
        rationale_result=extraction_result,
        model_name=active_model,
        token_ceiling=payload.max_tokens,
    )

    # Step 4: ADR Generation
    adr_result = generate_adrs(
        thread=cleaned_thread,
        verification_result=verification_result,
        rationale_result=extraction_result,
    )

    # Step 5: Persistence
    init_db()
    repo = StorageRepository()
    persist_info = repo.save_pipeline_result(
        thread=cleaned_thread,
        verification_result=verification_result,
        adr_result=adr_result,
        rationale_result=extraction_result,
    )

    return {
        "status": "success",
        "repository": cleaned_thread.repository,
        "entity_number": cleaned_thread.entity_number,
        "resource_type": cleaned_thread.resource_type,
        "source_url": cleaned_thread.html_url,
        "model_name": active_model,
        "detection": detection_result.to_dict(),
        "rationale": extraction_result.to_dict(),
        "verification": verification_result.to_dict(),
        "adrs": adr_result.to_dict(),
        "persisted": persist_info,
    }
