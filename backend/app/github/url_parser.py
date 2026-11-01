"""Re-export GitHub URL parser for architectural consistency."""

from app.github.parser import (
    GitHubResourceType,
    GitHubTarget,
    parse_github_url,
)

__all__ = ["GitHubTarget", "GitHubResourceType", "parse_github_url"]

