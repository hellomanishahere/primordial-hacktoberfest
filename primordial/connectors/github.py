"""GitHub connector for fetching and parsing issues, pull requests, and comments."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from typing import Any, Dict, List, Optional, Tuple

from primordial.connectors.base import BaseConnector
from primordial.connectors.dataset_loader import get_sample_discussion_by_url
from primordial.models import Comment, Discussion


class GitHubConnector(BaseConnector):
    """Fetches discussions from GitHub issues and pull requests."""

    URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?github\.com/(?P<owner>[\w\.\-]+)/(?P<repo>[\w\.\-]+)(?:/(?P<type>issues|pull)/(?P<number>\d+))?",
        re.IGNORECASE,
    )

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("GITHUB_TOKEN")

    def can_handle(self, source_url: str) -> bool:
        raw = source_url.strip()
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        return (parsed.hostname or "").lower() in {"github.com", "www.github.com"}

    def parse_url(self, source_url: str) -> Tuple[str, str, str, int]:
        raw = source_url.strip()
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        if (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
            raise ValueError("Expected a github.com issue or pull request URL")
        match = re.fullmatch(r"/([^/]+)/([^/]+)/(issues|pull)/(\d+)/?", parsed.path, re.IGNORECASE)
        if not match:
            raise ValueError("GitHub URL must identify a specific issue or pull request")
        owner, repo, item_type, number_text = match.groups()
        number = int(number_text)
        return owner, repo, item_type, number

    def _make_request(self, endpoint: str) -> Any:
        url = f"https://api.github.com/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Primordial-Decision-Intelligence/1.0",
        }
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_discussion(self, source_url: str) -> Discussion:
        # Check if local sample/fixture matches first
        sample = get_sample_discussion_by_url(source_url)
        if sample:
            return sample

        owner, repo, item_type, number = self.parse_url(source_url)
        canonical_url = f"https://github.com/{owner}/{repo}/{item_type}/{number}"
        disc_id = f"gh:{owner}/{repo}/{item_type}/{number}"

        try:
            # GitHub Issues API handles both issues and pull requests
            issue_data = self._make_request(f"repos/{owner}/{repo}/issues/{number}")
            title = issue_data.get("title", f"{owner}/{repo}#{number}")
            description = issue_data.get("body") or ""
            author = issue_data.get("user", {}).get("login", "anonymous")
            created_at = issue_data.get("created_at", "")
            closed_at = issue_data.get("closed_at")
            labels = [l.get("name", "") for l in issue_data.get("labels", [])]

            comments: List[Comment] = []

            # Fetch issue comments
            comments_data = self._make_request(
                f"repos/{owner}/{repo}/issues/{number}/comments?per_page=100"
            )
            for c in comments_data:
                c_id = str(c.get("id"))
                body = c.get("body") or ""
                reactions_dict = {}
                if "reactions" in c:
                    for k in ["+1", "-1", "laugh", "hooray", "confused", "heart", "rocket", "eyes"]:
                        count = c["reactions"].get(k, 0)
                        if count > 0:
                            reactions_dict[k] = count
                comments.append(
                    Comment(
                        id=f"gh-c-{c_id}",
                        author=c.get("user", {}).get("login", "unknown"),
                        created_at=c.get("created_at", ""),
                        body=body,
                        url=c.get("html_url", f"{canonical_url}#issuecomment-{c_id}"),
                        reactions=reactions_dict,
                    )
                )

            # If it's a pull request, also fetch PR review comments
            if item_type == "pull":
                try:
                    review_comments = self._make_request(
                        f"repos/{owner}/{repo}/pulls/{number}/comments?per_page=100"
                    )
                    for rc in review_comments:
                        rc_id = str(rc.get("id"))
                        body = rc.get("body") or ""
                        comments.append(
                            Comment(
                                id=f"gh-prc-{rc_id}",
                                author=rc.get("user", {}).get("login", "unknown"),
                                created_at=rc.get("created_at", ""),
                                body=body,
                                url=rc.get("html_url", f"{canonical_url}#discussion_r{rc_id}"),
                                reply_to_id=f"gh-prc-{rc.get('in_reply_to_id')}"
                                if rc.get("in_reply_to_id")
                                else None,
                            )
                        )
                except Exception:
                    pass

            return Discussion(
                id=disc_id,
                source_type="github",
                source_url=canonical_url,
                title=title,
                description=description,
                author=author,
                created_at=created_at,
                closed_at=closed_at,
                labels=labels,
                comments=comments,
                metadata={
                    "owner": owner,
                    "repo": repo,
                    "type": item_type,
                    "number": number,
                },
            )

        except Exception as e:
            raise RuntimeError(f"Could not fetch GitHub discussion {canonical_url}: {e}") from e
