"""GitHub URL validation, regex parsing, and target extraction."""

from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import urlparse
from app.core.exceptions import InvalidGitHubURLException


class GitHubResourceType(str, Enum):
    """Categorization of supported GitHub resources."""

    ISSUE = "issue"
    PULL_REQUEST = "pull_request"


@dataclass(frozen=True)
class GitHubTarget:
    """Strongly-typed representation of an extracted GitHub target."""

    owner: str
    repo: str
    entity_type: str  # "issues" or "pull"
    entity_number: int
    resource_type: GitHubResourceType

    @property
    def repository(self) -> str:
        """Owner and repository slug."""
        return f"{self.owner}/{self.repo}"

    @property
    def is_pull_request(self) -> bool:
        """Whether target is a pull request."""
        return self.resource_type == GitHubResourceType.PULL_REQUEST

    @property
    def is_issue(self) -> bool:
        """Whether target is an issue."""
        return self.resource_type == GitHubResourceType.ISSUE


# Matches /owner/repo/issues/123 or /owner/repo/pull/456
GITHUB_URL_PATH_REGEX = re.compile(
    r"^/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)/(?P<type>issues|pull)/(?P<number>\d+)$"
)


def parse_github_url(raw_url: str) -> GitHubTarget:
    """
    Parses and strictly validates a public GitHub Issue or Pull Request URL.

    Args:
        raw_url: Raw URL string entered by user or submitted via API.

    Returns:
        GitHubTarget: Strongly typed target identifying owner, repo, type, and number.

    Raises:
        InvalidGitHubURLException: If URL is malformed, from an unsupported host, or invalid structure.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise InvalidGitHubURLException(
            "GitHub URL cannot be empty or non-string",
            details={"url": raw_url},
        )

    clean_url = raw_url.strip()

    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        raise InvalidGitHubURLException(
            f"Malformed URL string: {exc}",
            details={"url": clean_url},
        )

    # Validate scheme (only http/https allowed; rejects file://, ftp://, etc.)
    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidGitHubURLException(
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are supported.",
            details={"url": clean_url, "scheme": parsed.scheme},
        )

    # Validate host (reject arbitrary hosts to prevent SSRF)
    host = parsed.netloc.split(":")[0].lower()
    if host not in ("github.com", "www.github.com"):
        raise InvalidGitHubURLException(
            f"Unsupported hostname '{host}'. Only github.com is supported.",
            details={"url": clean_url, "host": host},
        )

    # Clean path (strip trailing slashes)
    path = parsed.path.rstrip("/")

    match = GITHUB_URL_PATH_REGEX.match(path)
    if not match:
        raise InvalidGitHubURLException(
            "URL path must match the format /<owner>/<repo>/issues/<id> or /<owner>/<repo>/pull/<id>",
            details={"url": clean_url, "path": path},
        )

    owner = match.group("owner")
    repo = match.group("repo")
    raw_type = match.group("type")
    raw_number = match.group("number")

    # Strip .git suffix if repository was specified as repo.git
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Reject traversal or invalid identifiers
    if not owner or not repo or owner in (".", "..") or repo in (".", ".."):
        raise InvalidGitHubURLException(
            "Invalid repository owner or repository name identifier in URL",
            details={"url": clean_url, "owner": owner, "repo": repo},
        )

    try:
        number = int(raw_number)
        if number <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise InvalidGitHubURLException(
            f"Entity number must be a positive integer, got '{raw_number}'",
            details={"url": clean_url, "number": raw_number},
        )

    resource_type = (
        GitHubResourceType.PULL_REQUEST
        if raw_type == "pull"
        else GitHubResourceType.ISSUE
    )

    return GitHubTarget(
        owner=owner,
        repo=repo,
        entity_type=raw_type,
        entity_number=number,
        resource_type=resource_type,
    )

