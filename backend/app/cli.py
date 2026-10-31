"""Command-line interface entrypoint for Primordial."""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

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
from app.core.logging import setup_logging
from app.decision_detection.detector import detect_decisions
from app.github.client import GitHubClient
from app.github.normalizer import normalize_github_discussion
from app.github.parser import parse_github_url
from app.preprocessing.budgeter import format_discussion_transcript
from app.preprocessing.cleaner import clean_discussion_thread
from app.rationale_extraction.extractor import extract_decision_rationale
from app.evidence_verification.verifier import verify_evidence
from app.adr_generation.generator import generate_adrs
from app.adr_generation.templates import render_madr_markdown
from app.adr_generation.exporter import export_adr_to_file, export_all_adrs
from app.storage.repository import StorageRepository
from app.storage.database import init_db
from app.search.schemas import SearchFilters
from app.search.service import SearchService


async def fetch_and_normalize_url(url: str, output_path: Optional[str] = None):
    """Fetches a GitHub discussion from URL, normalizes it, and displays or writes the JSON output."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at timestamp: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        print("Tip: Provide a GITHUB_TOKEN in your environment or .env file to increase rate limits to 5,000 req/hr.", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"GitHub Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    data = thread.to_dict()

    print("\n--- Ingestion Summary ---")
    print(f"Title: {thread.title}")
    print(f"Author: @{thread.author}")
    print(f"State: {thread.state}")
    print(f"Created At: {thread.created_at.isoformat()}")
    print(f"Total Comments Ingested: {len(thread.comments)}")
    print(f"Direct Permalinks Preserved: {len(thread.comments)}")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nNormalized discussion saved to: {output_path}")
    else:
        print("\n--- Normalized Discussion Preview (First 2 Comments) ---")
        preview_data = dict(data)
        preview_data["comments"] = preview_data["comments"][:2]
        print(json.dumps(preview_data, indent=2))

    return thread


async def preprocess_discussion_url(
    url: str,
    output_path: Optional[str] = None,
    transcript_path: Optional[str] = None,
    max_tokens: int = 12000,
) -> None:
    """Fetches, cleans, and pre-processes a GitHub discussion into a sanitized chronological transcript."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting and preprocessing {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at timestamp: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        print("Tip: Provide a GITHUB_TOKEN in your environment or .env file to increase rate limits to 5,000 req/hr.", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Preprocessing Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Apply preprocessing filters and sanitization
    cleaned_thread = clean_discussion_thread(canonical_thread)
    transcript_text, budgeted_thread = format_discussion_transcript(cleaned_thread, token_ceiling=max_tokens)

    audit = budgeted_thread.audit
    print("\n--- Preprocessing & Filtering Audit ---")
    print(f"Total Comments Ingested: {audit.total_comments_input}")
    print(f"Substantive Comments Retained: {audit.substantive_comments_retained}")
    print(f"Comments Removed: {audit.comments_removed}")
    print(f"Discussion Is Empty: {audit.is_empty}")
    print(f"Context Truncated: {audit.was_truncated}")
    print(f"Estimated Tokens: {budgeted_thread.estimated_tokens}")

    if audit.removal_records:
        print(f"\nRemoved Comments ({len(audit.removal_records)}):")
        for record in audit.removal_records[:5]:
            print(f"  - [{record.comment_id}] @{record.author}: {record.reason.value} ({record.details or ''})")
        if len(audit.removal_records) > 5:
            print(f"  ... and {len(audit.removal_records) - 5} more.")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(budgeted_thread.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\nCleaned discussion saved to: {output_path}")

    if transcript_path:
        os.makedirs(os.path.dirname(os.path.abspath(transcript_path)), exist_ok=True)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"Formatted transcript saved to: {transcript_path}")

    if not output_path and not transcript_path:
        print("\n--- Formatted Transcript Preview (First 500 characters) ---")
        print(transcript_text[:500] + ("..." if len(transcript_text) > 500 else ""))


async def detect_decisions_url(
    url: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 12000,
) -> None:
    """Fetches, preprocesses, and runs AI decision detection on a GitHub discussion."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at timestamp: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        print("Tip: Provide a GITHUB_TOKEN in your environment or .env file to increase rate limits to 5,000 req/hr.", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"GitHub Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    # Preprocess discussion
    cleaned_thread = clean_discussion_thread(canonical_thread)

    active_model = model or settings.AI_MODEL_PRIMARY
    print(f"Running decision detection with AI model '{active_model}'...")

    try:
        detection_result = await detect_decisions(
            cleaned_thread,
            model_name=active_model,
            token_ceiling=max_tokens,
        )
    except AIServiceUnavailableException as exc:
        print(f"AI Service Error: {exc.message}", file=sys.stderr)
        print("Tip: Ensure the local Ollama daemon is active (`ollama serve`) and the model is downloaded (`ollama pull " + active_model + "`).", file=sys.stderr)
        sys.exit(1)
    except AIModelTimeoutException as exc:
        print(f"AI Timeout Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (AIModelResponseException, SchemaValidationException) as exc:
        print(f"AI Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected detection error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Display detection summary
    print("\n--- AI Decision Detection Summary ---")
    print(f"Repository: {detection_result.repository}")
    print(f"Discussion: #{detection_result.entity_number} ({detection_result.resource_type})")
    print(f"Model: {detection_result.model_name}")
    print(f"Decision Detected: {'YES' if detection_result.is_decision_detected else 'NO'}")
    print(f"Total Candidate Decisions: {detection_result.total_decisions}")

    if detection_result.decisions:
        print("\nCandidate Decisions:")
        for dec in detection_result.decisions:
            print(f"\n  • [{dec.decision_id}] [{dec.status.value.upper()}] (Confidence: {dec.confidence:.2f})")
            print(f"    Statement: {dec.decision_statement}")
            print(f"    Supporting Comments: {', '.join(dec.supporting_comment_ids)}")

    if detection_result.processing_notes:
        print("\nProcessing & Audit Notes:")
        for note in detection_result.processing_notes:
            print(f"  - {note}")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(detection_result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\nDetection results saved to: {output_path}")
    else:
        print("\n--- Full JSON Output ---")
        print(json.dumps(detection_result.to_dict(), indent=2, ensure_ascii=False))


async def extract_rationale_url(
    url: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 12000,
) -> None:
    """Fetches, preprocesses, detects decisions, and extracts rationale for a GitHub discussion."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        print("Tip: Provide a GITHUB_TOKEN in your environment to increase rate limits.", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"GitHub Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    # Preprocess discussion
    cleaned_thread = clean_discussion_thread(canonical_thread)
    active_model = model or settings.AI_MODEL_PRIMARY

    # Run decision detection (Module 4)
    print(f"Running decision detection with model '{active_model}'...")
    try:
        detection_result = await detect_decisions(cleaned_thread, model_name=active_model, token_ceiling=max_tokens)
    except AIServiceUnavailableException as exc:
        print(f"AI Service Error: {exc.message}", file=sys.stderr)
        print(f"Tip: Ensure Ollama is running (`ollama serve`) and the model is available (`ollama pull {active_model}`).", file=sys.stderr)
        sys.exit(1)
    except AIModelTimeoutException as exc:
        print(f"AI Timeout Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (AIModelResponseException, SchemaValidationException) as exc:
        print(f"AI Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected detection error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  Decisions detected: {'YES' if detection_result.is_decision_detected else 'NO'} ({detection_result.total_decisions} candidate(s))")

    # Run rationale extraction (Module 5)
    print(f"Extracting rationale and arguments with model '{active_model}'...")
    try:
        extraction_result = await extract_decision_rationale(
            thread=cleaned_thread,
            detection_result=detection_result,
            model_name=active_model,
            token_ceiling=max_tokens,
        )
    except AIServiceUnavailableException as exc:
        print(f"AI Service Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except AIModelTimeoutException as exc:
        print(f"AI Timeout Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (AIModelResponseException, SchemaValidationException) as exc:
        print(f"AI Extraction Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Extraction Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected extraction error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Display summary
    print("\n--- Rationale Extraction Summary ---")
    print(f"Repository:          {extraction_result.repository}")
    print(f"Discussion:          #{extraction_result.entity_number} ({extraction_result.resource_type})")
    print(f"Model:               {extraction_result.model_name}")
    print(f"Decisions Evaluated: {extraction_result.decisions_evaluated}")
    print(f"Rationale Extracted: {'YES' if extraction_result.is_rationale_extracted else 'NO'}")
    print(f"Evidence Citations:  {extraction_result.total_evidence_citations} comment(s)")

    if extraction_result.rationales:
        print("\nExtracted Rationale Records:")
        for rat in extraction_result.rationales:
            print(f"\n  • [{rat.decision_id}] [{rat.status.upper()}] (Confidence: {rat.confidence:.2f})")
            print(f"    Summary:  {rat.decision_summary}")
            print(f"    Rationale: {rat.rationale.statement}")
            if rat.supporting_arguments:
                print(f"    Supporting Arguments: {len(rat.supporting_arguments)}")
            if rat.opposing_arguments:
                print(f"    Opposing Arguments:   {len(rat.opposing_arguments)}")
            if rat.rejected_alternatives:
                print(f"    Rejected Alternatives: {len(rat.rejected_alternatives)}")
            if rat.trade_offs:
                print(f"    Trade-offs:           {len(rat.trade_offs)}")
            if rat.consequences:
                print(f"    Consequences:         {len(rat.consequences)}")
            print(f"    Evidence Comment IDs: {', '.join(rat.evidence_comment_ids) or 'none'}")

    if extraction_result.processing_notes:
        print("\nProcessing & Audit Notes:")
        for note in extraction_result.processing_notes:
            print(f"  - {note}")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extraction_result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\nRationale extraction saved to: {output_path}")
    else:
        print("\n--- Full JSON Output ---")
        print(json.dumps(extraction_result.to_dict(), indent=2, ensure_ascii=False))


async def verify_evidence_url(
    url: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 12000,
) -> None:
    """Fetches, preprocesses, detects decisions, extracts rationale, and verifies evidence for a GitHub discussion."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        print("Tip: Provide a GITHUB_TOKEN in your environment to increase rate limits.", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"GitHub Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    cleaned_thread = clean_discussion_thread(canonical_thread)
    active_model = model or settings.AI_MODEL_PRIMARY

    # Decision detection
    print(f"Running decision detection with model '{active_model}'...")
    try:
        detection_result = await detect_decisions(cleaned_thread, model_name=active_model, token_ceiling=max_tokens)
    except AIServiceUnavailableException as exc:
        print(f"AI Service Error: {exc.message}", file=sys.stderr)
        print(f"Tip: Ensure Ollama is running (`ollama serve`) and the model is available (`ollama pull {active_model}`).", file=sys.stderr)
        sys.exit(1)
    except AIModelTimeoutException as exc:
        print(f"AI Timeout Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (AIModelResponseException, SchemaValidationException) as exc:
        print(f"AI Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Detection Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected detection error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Rationale extraction
    print(f"Extracting rationale and arguments with model '{active_model}'...")
    try:
        extraction_result = await extract_decision_rationale(
            thread=cleaned_thread,
            detection_result=detection_result,
            model_name=active_model,
            token_ceiling=max_tokens,
        )
    except AIServiceUnavailableException as exc:
        print(f"AI Service Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except AIModelTimeoutException as exc:
        print(f"AI Timeout Error: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (AIModelResponseException, SchemaValidationException) as exc:
        print(f"AI Extraction Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"Extraction Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected extraction error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Evidence verification (Module 7)
    print("Verifying evidence and authentic comment provenance...")
    verification_result = await verify_evidence(
        thread=cleaned_thread,
        rationale_result=extraction_result,
        model_name=active_model,
        token_ceiling=max_tokens,
    )

    # Display summary
    print("\n--- Evidence Verification Summary ---")
    print(f"Repository:               {verification_result.repository}")
    print(f"Discussion:               #{verification_result.entity_number} ({verification_result.resource_type})")
    print(f"Decisions Evaluated:      {verification_result.decisions_evaluated}")
    print(f"Claims Verified:          {verification_result.total_claims_verified}")
    print(f"Claims Contradicted:      {verification_result.total_claims_contradicted}")
    print(f"Claims Unsupported:       {verification_result.total_claims_unsupported}")

    if verification_result.verified_decisions:
        print("\nVerified Decision Records:")
        for vdec in verification_result.verified_decisions:
            print(f"\n  • [{vdec.decision_id}] [{vdec.overall_verification_status.value.upper()}] (Confidence: {vdec.confidence:.2f})")
            print(f"    Summary: {vdec.decision_summary}")
            print(f"    Claims Evaluated: {vdec.total_claims_evaluated} (Verified: {vdec.verified_claims_count}, Partially Supported: {vdec.partially_supported_count}, Contradicted: {vdec.contradicted_count}, Unsupported: {vdec.unsupported_count})")
            print(f"    Supporting Comments: {', '.join(vdec.all_supporting_comment_ids) or 'none'}")
            if vdec.all_contradicting_comment_ids:
                print(f"    Contradicting Comments: {', '.join(vdec.all_contradicting_comment_ids)}")

            for claim in vdec.claim_verifications:
                print(f"      - [{claim.status.value.upper()}] ({claim.evidence_type.value}) {claim.claim_type}: \"{claim.claim_text[:60]}...\"")
                if claim.supporting_comment_ids:
                    print(f"        Evidence: Comment IDs {claim.supporting_comment_ids}")
                if claim.contradicting_comment_ids:
                    print(f"        Contradicted By: Comment IDs {claim.contradicting_comment_ids}")

    if verification_result.processing_notes:
        print("\nProcessing & Audit Notes:")
        for note in verification_result.processing_notes:
            print(f"  - {note}")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(verification_result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\nEvidence verification saved to: {output_path}")
    else:
        print("\n--- Full JSON Output ---")
        print(json.dumps(verification_result.to_dict(), indent=2, ensure_ascii=False))


async def generate_adr_url(
    url: str,
    output_path: Optional[str] = None,
    output_format: str = "markdown",
    model: Optional[str] = None,
    max_tokens: int = 12000,
) -> None:
    """End-to-end pipeline: Fetch -> Preprocess -> Detect -> Extract Rationale -> Verify Evidence -> Generate ADR."""
    try:
        target = parse_github_url(url)
    except InvalidGitHubURLException as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {target.resource_type.value} from {target.repository} #{target.entity_number}...")

    try:
        async with GitHubClient() as client:
            raw_data = await client.fetch_discussion(target)
            canonical_thread = normalize_github_discussion(target, raw_data)
    except GitHubRateLimitExceededException as exc:
        reset_info = f" (Resets at: {exc.details.get('rate_limit_reset')})" if exc.details.get("rate_limit_reset") else ""
        print(f"Rate Limit Error: {exc.message}{reset_info}", file=sys.stderr)
        sys.exit(1)
    except GitHubResourceNotFoundException as exc:
        print(f"Not Found: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except PrimordialException as exc:
        print(f"GitHub Ingestion Error: [{exc.error_code}] {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    cleaned_thread = clean_discussion_thread(canonical_thread)
    active_model = model or settings.AI_MODEL_PRIMARY

    # Step 1: Decision detection
    print(f"Running decision detection with model '{active_model}'...")
    try:
        detection_result = await detect_decisions(cleaned_thread, model_name=active_model, token_ceiling=max_tokens)
    except (AIServiceUnavailableException, AIModelTimeoutException, AIModelResponseException, SchemaValidationException, PrimordialException) as exc:
        print(f"Detection Error: {exc.message if hasattr(exc, 'message') else exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected detection error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Rationale extraction
    print(f"Extracting rationale and arguments with model '{active_model}'...")
    try:
        extraction_result = await extract_decision_rationale(
            thread=cleaned_thread,
            detection_result=detection_result,
            model_name=active_model,
            token_ceiling=max_tokens,
        )
    except (AIServiceUnavailableException, AIModelTimeoutException, AIModelResponseException, SchemaValidationException, PrimordialException) as exc:
        print(f"Extraction Error: {exc.message if hasattr(exc, 'message') else exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected extraction error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Evidence verification
    print("Verifying evidence and authentic comment provenance...")
    verification_result = await verify_evidence(
        thread=cleaned_thread,
        rationale_result=extraction_result,
        model_name=active_model,
        token_ceiling=max_tokens,
    )

    # Step 4: ADR generation
    print("Compiling MADR Architecture Decision Records...")
    adr_result = generate_adrs(
        thread=cleaned_thread,
        verification_result=verification_result,
        rationale_result=extraction_result,
    )

    # Step 5: Persist to storage (Module 9)
    try:
        init_db()
        repo = StorageRepository()
        persist_info = repo.save_pipeline_result(
            thread=cleaned_thread,
            verification_result=verification_result,
            adr_result=adr_result,
            rationale_result=extraction_result,
        )
        print(f"Persisted to knowledge store: {persist_info['saved_decisions_count']} decision(s) saved.")
    except Exception as exc:
        print(f"Warning: Storage persistence failed: {exc}", file=sys.stderr)

    print("\n--- ADR Generation Summary ---")
    print(f"Repository:     {adr_result.repository}")
    print(f"Discussion:     #{adr_result.entity_number}")
    print(f"Total ADRs:     {adr_result.total_adrs}")

    if not adr_result.adrs:
        print("\nNo engineering decisions detected or verified to compile into ADRs.")
        return

    for adr in adr_result.adrs:
        print(f"\n[{adr.adr_id}] {adr.title}")
        print(f"  Status:               {adr.status.value.upper()}")
        print(f"  Date:                 {adr.date}")
        print(f"  Decision Outcome:     {adr.decision}")
        print(f"  Supporting Evidence:  {len(adr.supporting_evidence)} citation(s)")
        print(f"  Considered Options:   {len(adr.considered_alternatives)} rejected alternative(s)")
        print(f"  Markdown File Slug:   {adr.file_slug}.md")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(adr_result.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            # If multiple ADRs, write first or combined
            combined_md = "\n\n---\n\n".join(render_madr_markdown(a) for a in adr_result.adrs)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(combined_md)
        print(f"\nADR document(s) saved to: {output_path}")
    else:
        print("\n--- MADR 3.0.0 Markdown Preview ---")
        for adr in adr_result.adrs:
            print("\n" + render_madr_markdown(adr))


def search_decisions_cli(
    query: str,
    repository: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> None:
    """Executes a search against persisted historical engineering decisions."""
    init_db()
    service = SearchService()
    filters = SearchFilters(
        repository=repository,
        status=status,
        limit=limit,
    )
    result = service.search(query=query, filters=filters)

    print(f"\n--- Decision Search Results: '{query}' ---")
    print(f"Total Matches: {result.total_hits}\n")

    if not result.hits:
        print("No historical engineering decisions matched your query.")
        return

    for hit in result.hits:
        print(f"• [{hit.decision_id}] [{hit.status.upper()}] {hit.title}")
        print(f"  Repository:  {hit.repository} #{hit.entity_number}")
        print(f"  Summary:     {hit.summary}")
        if hit.adr_id:
            print(f"  ADR Record:  {hit.adr_id}")
        if hit.match_snippet:
            print(f"  Snippet:     {hit.match_snippet}")
        print(f"  Source URL:  {hit.source_url}\n")


def list_decisions_cli(
    repository: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> None:
    """Lists persisted engineering decisions in the database."""
    init_db()
    repo = StorageRepository()
    decisions = repo.list_decisions(repository=repository, status=status, limit=limit)

    print(f"\n--- Persisted Engineering Decisions (Total: {len(decisions)}) ---")
    if not decisions:
        print("No decisions recorded yet. Run `primordial generate-adr <url>` to ingest discussions.")
        return

    for d in decisions:
        adr_str = f" [ADR: {d['adr_id']}]" if d.get("adr_id") else ""
        print(f"• [{d['decision_id']}] [{d['status'].upper()}]{adr_str} {d['decision_summary']}")
        print(f"  Repository: {d['repository']} #{d['entity_number']} | URL: {d['html_url']}")


def show_decision_cli(decision_id: str) -> None:
    """Displays comprehensive details, provenance, and claims for a single decision."""
    init_db()
    repo = StorageRepository()
    dec = repo.get_decision(decision_id)

    if not dec:
        print(f"Error: Decision '{decision_id}' not found in database.", file=sys.stderr)
        sys.exit(1)

    print(f"\n--- Decision Record: {dec['decision_id']} ---")
    print(f"Summary:       {dec['decision_summary']}")
    print(f"Status:        {dec['status'].upper()}")
    print(f"Confidence:    {dec['confidence']}")
    print(f"Repository:    {dec['repository']} #{dec['entity_number']}")
    print(f"Source URL:    {dec['html_url']}")

    if dec.get("claims"):
        print("\nClaims & Arguments:")
        for c in dec["claims"]:
            cids = json.loads(c["supporting_comment_ids"]) if c.get("supporting_comment_ids") else []
            print(f"  - [{c['claim_type'].upper()}] [{c['evidence_status'].upper()}] \"{c['statement']}\"")
            if cids:
                print(f"    Evidence Comment IDs: {', '.join(cids)}")

    if dec.get("alternatives"):
        print("\nRejected Alternatives:")
        for alt in dec["alternatives"]:
            print(f"  - {alt['title']}: {alt['rejection_reason']} ([{alt['verification_status'].upper()}])")

    if dec.get("adr"):
        adr = dec["adr"]
        print(f"\nAssociated ADR: {adr['adr_id']} ({adr['file_slug']})")


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    parser = argparse.ArgumentParser(
        prog="primordial",
        description="Primordial: Open Source Decision Intelligence and Knowledge Recovery",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Primordial v{settings.VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Fetch command (Module 2)
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch and normalize a GitHub Issue or Pull Request discussion without AI processing",
    )
    fetch_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    fetch_parser.add_argument("--output", "-o", help="Optional path to write normalized JSON output file")

    # Preprocess command (Module 3)
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        help="Clean, filter noise/bots, and format a GitHub discussion into a citation transcript",
    )
    preprocess_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    preprocess_parser.add_argument("--output", "-o", help="Optional path to write cleaned JSON output file")
    preprocess_parser.add_argument("--transcript", "-t", help="Optional path to write formatted transcript text file")
    preprocess_parser.add_argument("--max-tokens", type=int, default=12000, help="Context token ceiling (default: 12000)")

    # Detect command (Module 4)
    detect_parser = subparsers.add_parser(
        "detect",
        help="Run AI decision detection on a GitHub discussion to identify engineering decisions",
    )
    detect_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    detect_parser.add_argument("--output", "-o", help="Optional path to write detection JSON output file")
    detect_parser.add_argument("--model", "-m", help=f"Ollama AI model to execute (default: {settings.AI_MODEL_PRIMARY})")
    detect_parser.add_argument("--max-tokens", type=int, default=12000, help="Context token ceiling (default: 12000)")

    # Extract-rationale command (Module 5)
    extract_rationale_parser = subparsers.add_parser(
        "extract-rationale",
        help="Detect engineering decisions and extract rationale, arguments, alternatives, and trade-offs",
    )
    extract_rationale_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    extract_rationale_parser.add_argument("--output", "-o", help="Optional path to write rationale JSON output file")
    extract_rationale_parser.add_argument("--model", "-m", help=f"Ollama AI model to execute (default: {settings.AI_MODEL_PRIMARY})")
    extract_rationale_parser.add_argument("--max-tokens", type=int, default=12000, help="Context token ceiling (default: 12000)")

    # Verify-evidence command (Module 7)
    verify_evidence_parser = subparsers.add_parser(
        "verify-evidence",
        help="Verify evidence grounding and authentic provenance for extracted decisions and rationales",
    )
    verify_evidence_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    verify_evidence_parser.add_argument("--output", "-o", help="Optional path to write verification JSON output file")
    verify_evidence_parser.add_argument("--model", "-m", help=f"Ollama AI model to execute (default: {settings.AI_MODEL_PRIMARY})")
    verify_evidence_parser.add_argument("--max-tokens", type=int, default=12000, help="Context token ceiling (default: 12000)")

    # Generate-adr command (Module 8)
    generate_adr_parser = subparsers.add_parser(
        "generate-adr",
        help="Generate structured MADR Architecture Decision Records from verified GitHub discussions",
    )
    generate_adr_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    generate_adr_parser.add_argument("--output", "-o", help="Optional path to write ADR output file")
    generate_adr_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (markdown or json, default: markdown)")
    generate_adr_parser.add_argument("--model", "-m", help=f"Ollama AI model to execute (default: {settings.AI_MODEL_PRIMARY})")
    generate_adr_parser.add_argument("--max-tokens", type=int, default=12000, help="Context token ceiling (default: 12000)")

    # Search command (Module 9)
    search_parser = subparsers.add_parser(
        "search",
        help="Search persisted historical engineering decisions using full-text and metadata indexing",
    )
    search_parser.add_argument("query", help="Search keywords, concepts, or technology terms")
    search_parser.add_argument("--repo", help="Filter by repository (owner/repo)")
    search_parser.add_argument("--status", help="Filter by status (accepted, proposed, rejected, deferred, unclear)")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results to return (default: 20)")

    # List-decisions command (Module 9)
    list_dec_parser = subparsers.add_parser(
        "list-decisions",
        help="List all persisted engineering decisions in the local knowledge base",
    )
    list_dec_parser.add_argument("--repo", help="Filter by repository (owner/repo)")
    list_dec_parser.add_argument("--status", help="Filter by status (accepted, proposed, rejected, deferred, unclear)")
    list_dec_parser.add_argument("--limit", type=int, default=50, help="Max results to return (default: 50)")

    # Show-decision command (Module 9)
    show_dec_parser = subparsers.add_parser(
        "show-decision",
        help="Display comprehensive details, claims, alternatives, and ADR for a single decision ID",
    )
    show_dec_parser.add_argument("decision_id", help="Decision ID (e.g. dec-123-1)")

    # Extract command (Planned for later modules)
    extract_parser = subparsers.add_parser("extract", help="Recover decisions from a GitHub discussion URL")
    extract_parser.add_argument("url", help="Public GitHub Issue or Pull Request URL")
    extract_parser.add_argument("--output", "-o", help="Path to write compiled MADR output file")
    extract_parser.add_argument("--format", choices=["madr", "json"], default="madr", help="Output format")
    extract_parser.add_argument("--fixture", help="Path to local JSON fixture for offline demo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "fetch":
        asyncio.run(fetch_and_normalize_url(args.url, args.output))
    elif args.command == "preprocess":
        asyncio.run(
            preprocess_discussion_url(
                args.url,
                output_path=args.output,
                transcript_path=args.transcript,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "detect":
        asyncio.run(
            detect_decisions_url(
                args.url,
                output_path=args.output,
                model=args.model,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "extract-rationale":
        asyncio.run(
            extract_rationale_url(
                args.url,
                output_path=args.output,
                model=args.model,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "verify-evidence":
        asyncio.run(
            verify_evidence_url(
                args.url,
                output_path=args.output,
                model=args.model,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "generate-adr":
        asyncio.run(
            generate_adr_url(
                args.url,
                output_path=args.output,
                output_format=args.format,
                model=args.model,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "search":
        search_decisions_cli(
            query=args.query,
            repository=args.repo,
            status=args.status,
            limit=args.limit,
        )
    elif args.command == "list-decisions":
        list_decisions_cli(
            repository=args.repo,
            status=args.status,
            limit=args.limit,
        )
    elif args.command == "show-decision":
        show_decision_cli(args.decision_id)
    elif args.command == "extract":
        print(f"Primordial extraction requested for: {args.url}")
        print("Note: Core pipeline AI decision extraction will be implemented in subsequent modules.")


if __name__ == "__main__":
    main()
