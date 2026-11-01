"""Pull request metadata and file diff ingestion for PR Radar (Module 10)."""

from typing import List, Optional
from app.core.exceptions import InvalidGitHubURLException, PrimordialException
from app.core.logging import get_logger
from app.github.client import GitHubClient
from app.github.parser import GitHubResourceType, parse_github_url
from app.pr_radar.schemas import ChangedFile, PullRequestAnalysis

logger = get_logger("pr_radar.analyzer")


class PullRequestAnalyzer:
    """Ingests and structures Pull Request metadata and file diffs for radar analysis."""

    def __init__(self, github_client: Optional[GitHubClient] = None) -> None:
        self.github_client = github_client

    async def analyze_url(self, url: str) -> PullRequestAnalysis:
        """
        Parses PR URL, retrieves PR details and modified files from GitHub API.
        """
        target = parse_github_url(url)
        if target.resource_type != GitHubResourceType.PULL_REQUEST:
            raise InvalidGitHubURLException(
                message="Historical PR Radar requires a GitHub Pull Request URL (not an issue)",
                details={"url": url},
            )

        owner = target.owner
        repo = target.repo
        number = target.entity_number

        if self.github_client:
            return await self._fetch_pr(self.github_client, owner, repo, number, url)

        async with GitHubClient() as client:
            return await self._fetch_pr(client, owner, repo, number, url)

    async def _fetch_pr(
        self,
        client: GitHubClient,
        owner: str,
        repo: str,
        number: int,
        url: str,
    ) -> PullRequestAnalysis:
        raw_pr = await client.fetch_pull_request(owner, repo, number)

        # Ingest changed files (gracefully handling errors or missing permissions)
        changed_files: List[ChangedFile] = []
        try:
            raw_files = await client.fetch_pull_request_files(owner, repo, number)
            for f in raw_files:
                changed_files.append(
                    ChangedFile(
                        filename=f.get("filename", ""),
                        status=f.get("status", "modified"),
                        additions=f.get("additions", 0),
                        deletions=f.get("deletions", 0),
                        patch=f.get("patch"),
                    )
                )
        except Exception as exc:
            logger.warning("Could not retrieve file diffs for %s/%s#%d: %s", owner, repo, number, exc)

        return PullRequestAnalysis(
            repository=f"{owner}/{repo}",
            pr_number=number,
            title=raw_pr.get("title", ""),
            url=raw_pr.get("html_url", url),
            author=raw_pr.get("user", {}).get("login", "unknown"),
            description=raw_pr.get("body") or "",
            changed_files=changed_files,
        )
