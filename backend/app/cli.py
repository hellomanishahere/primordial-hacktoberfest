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
    elif args.command == "extract":
        print(f"Primordial extraction requested for: {args.url}")
        print("Note: Core pipeline AI decision extraction will be implemented in subsequent modules.")


if __name__ == "__main__":
    main()
