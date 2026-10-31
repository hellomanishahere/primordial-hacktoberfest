"""Command-line interface entrypoint for Primordial."""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

from app.core.config import settings
from app.core.exceptions import (
    GitHubRateLimitExceededException,
    GitHubResourceNotFoundException,
    InvalidGitHubURLException,
    PrimordialException,
)
from app.core.logging import setup_logging
from app.github.client import GitHubClient
from app.github.normalizer import normalize_github_discussion
from app.github.parser import parse_github_url


async def fetch_and_normalize_url(url: str, output_path: Optional[str] = None) -> None:
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
    elif args.command == "extract":
        print(f"Primordial extraction requested for: {args.url}")
        print("Note: Core pipeline AI decision extraction will be implemented in subsequent modules.")


if __name__ == "__main__":
    main()
