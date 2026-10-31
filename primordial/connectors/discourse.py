"""Discourse connector for fetching and parsing forum topics and posts."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from primordial.connectors.base import BaseConnector
from primordial.connectors.dataset_loader import get_sample_discussion_by_url
from primordial.models import Comment, Discussion


class DiscourseConnector(BaseConnector):
    """Fetches discussions from Discourse forum topics."""

    # Matches https://meta.discourse.org/t/some-topic-slug/12345 or /t/12345 or root domain discuss.python.org
    URL_PATTERN = re.compile(
        r"(?:https?://)?(?P<domain>[a-zA-Z0-9\.\-]+?)(?:/t/(?:(?P<slug>[a-zA-Z0-9\-_]+)/)?(?P<topic_id>\d+))?/?$",
        re.IGNORECASE,
    )

    def __init__(self, api_key: Optional[str] = None, api_username: Optional[str] = None):
        self.api_key = api_key
        self.api_username = api_username

    def can_handle(self, source_url: str) -> bool:
        raw = source_url.strip()
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.hostname.lower() in {"github.com", "www.github.com"}:
            return False
        return bool(re.fullmatch(r"/t/(?:[a-zA-Z0-9_-]+/)?\d+/?", parsed.path))

    def parse_url(self, source_url: str) -> Tuple[str, Optional[str], int]:
        raw = source_url.strip()
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        domain = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"} or not domain or domain.lower() in {"github.com", "www.github.com"}:
            raise ValueError("Expected a public Discourse topic URL")
        match = re.fullmatch(r"/t/(?:([a-zA-Z0-9_-]+)/)?(\d+)/?", parsed.path)
        if not match:
            raise ValueError("Discourse URL must identify a specific topic")
        slug, tid_str = match.groups()
        topic_id = int(tid_str)
        return (domain, slug, topic_id)

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from cooked Discourse output if raw markdown not present."""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _make_request(self, domain: str, topic_id: int) -> Dict[str, Any]:
        url = f"https://{domain}/t/{topic_id}.json"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Primordial-Decision-Intelligence/1.0",
        }
        if self.api_key and self.api_username:
            headers["Api-Key"] = self.api_key
            headers["Api-Username"] = self.api_username

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_discussion(self, source_url: str) -> Discussion:
        # Check local sample fixture first
        sample = get_sample_discussion_by_url(source_url)
        if sample:
            return sample

        domain, slug, topic_id = self.parse_url(source_url)
        canonical_url = f"https://{domain}/t/{slug or 'topic'}/{topic_id}"
        disc_id = f"dc:{domain}/t/{topic_id}"

        try:
            data = self._make_request(domain, topic_id)
            title = data.get("title", f"Discourse Topic #{topic_id}")
            created_at = data.get("created_at", "")
            closed = data.get("closed", False)
            closed_at = data.get("closed_at") if closed else None
            tags = data.get("tags", [])

            post_stream = data.get("post_stream", {})
            posts = post_stream.get("posts", [])

            if not posts:
                raise ValueError("No posts found in Discourse topic response")

            op_post = posts[0]
            op_body = op_post.get("raw") or self._strip_html(op_post.get("cooked", ""))
            author = op_post.get("username", "anonymous")

            comments: List[Comment] = []
            for post in posts[1:]:
                p_num = post.get("post_number", 0)
                body = post.get("raw") or self._strip_html(post.get("cooked", ""))
                post_url = f"{canonical_url}/{p_num}"
                reply_to_num = post.get("reply_to_post_number")

                reactions = {}
                for action in post.get("actions_summary", []):
                    if action.get("id") == 2:
                        reactions["like"] = action.get("count", 0)

                comments.append(
                    Comment(
                        id=f"dc-p-{post.get('id')}",
                        author=post.get("username", "unknown"),
                        created_at=post.get("created_at", ""),
                        body=body,
                        url=post_url,
                        reply_to_id=f"dc-p-num-{reply_to_num}" if reply_to_num else None,
                        reactions=reactions,
                    )
                )

            return Discussion(
                id=disc_id,
                source_type="discourse",
                source_url=canonical_url,
                title=title,
                description=op_body,
                author=author,
                created_at=created_at,
                closed_at=closed_at,
                labels=tags,
                comments=comments,
                metadata={
                    "domain": domain,
                    "topic_id": topic_id,
                    "slug": slug,
                    "views": data.get("views", 0),
                    "like_count": data.get("like_count", 0),
                },
            )

        except Exception as e:
            raise RuntimeError(f"Could not fetch Discourse discussion {canonical_url}: {e}") from e
