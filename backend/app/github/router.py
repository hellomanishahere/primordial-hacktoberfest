"""Entity routing and execution plan construction (Issues vs. Pull Requests)."""

from dataclasses import dataclass
from typing import Optional
from app.github.parser import GitHubTarget


@dataclass(frozen=True)
class ExecutionPlan:
    """Execution plan detailing which GitHub API endpoints to query for a given target."""

    target: GitHubTarget
    metadata_endpoint: str
    comments_endpoint: str
    review_comments_endpoint: Optional[str] = None
    reviews_endpoint: Optional[str] = None

    @property
    def is_pull_request(self) -> bool:
        """Whether the target plan queries pull request specific resources."""
        return self.target.is_pull_request


def create_execution_plan(target: GitHubTarget) -> ExecutionPlan:
    """
    Constructs an API query execution plan based on whether the entity is an Issue or Pull Request.

    Args:
        target: Validated GitHub target.

    Returns:
        ExecutionPlan specifying exact REST resource paths to fetch.
    """
    owner = target.owner
    repo = target.repo
    number = target.entity_number

    if target.is_pull_request:
        return ExecutionPlan(
            target=target,
            metadata_endpoint=f"/repos/{owner}/{repo}/pulls/{number}",
            comments_endpoint=f"/repos/{owner}/{repo}/issues/{number}/comments",
            review_comments_endpoint=f"/repos/{owner}/{repo}/pulls/{number}/comments",
            reviews_endpoint=f"/repos/{owner}/{repo}/pulls/{number}/reviews",
        )

    return ExecutionPlan(
        target=target,
        metadata_endpoint=f"/repos/{owner}/{repo}/issues/{number}",
        comments_endpoint=f"/repos/{owner}/{repo}/issues/{number}/comments",
        review_comments_endpoint=None,
        reviews_endpoint=None,
    )

