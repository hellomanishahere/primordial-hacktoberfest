"""Discourse connector for fetching and parsing forum topics and posts."""
from __future__ import annotations

import json
import http.client
import ipaddress
import re
import socket
import ssl
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from primordial.connectors.base import BaseConnector
from primordial.connectors.dataset_loader import get_sample_discussion_by_url
from primordial.models import Comment, Discussion


MAX_RESPONSE_BYTES = 2_000_000
REQUEST_TIMEOUT_SECONDS = 10


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a previously validated public IP while retaining TLS hostname checks."""

    def __init__(self, hostname: str, address: str):
        super().__init__(hostname, port=443, timeout=REQUEST_TIMEOUT_SECONDS,
                         context=ssl.create_default_context())
        self._resolved_address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._resolved_address, self.port), timeout=self.timeout
        )
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


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
        try:
            self.parse_url(source_url)
        except (TypeError, ValueError):
            return False
        return True

    def parse_url(self, source_url: str) -> Tuple[str, Optional[str], int]:
        raw = source_url.strip()
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        domain = parsed.hostname or ""
        if (
            parsed.scheme != "https"
            or not domain
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.query
            or parsed.fragment
            or domain.lower() in {"github.com", "www.github.com"}
        ):
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
        try:
            resolved = socket.getaddrinfo(
                domain, 443, type=socket.SOCK_STREAM
            )
        except socket.gaierror as exc:
            raise ValueError("Discussion host could not be resolved") from exc

        addresses = list(dict.fromkeys(info[4][0] for info in resolved))
        if not addresses:
            raise ValueError("Discussion host has no reachable address")
        for address in addresses:
            try:
                is_public = ipaddress.ip_address(address.split("%", 1)[0]).is_global
            except ValueError:
                is_public = False
            if not is_public:
                raise ValueError("Discussion host resolves to a non-public address")

        headers = {
            "Accept": "application/json",
            "User-Agent": "Primordial-Decision-Intelligence/1.0",
        }
        if self.api_key and self.api_username:
            headers["Api-Key"] = self.api_key
            headers["Api-Username"] = self.api_username

        # Pin the connection to the address we validated so a DNS change between
        # validation and connect cannot redirect this request to a private host.
        with _PinnedHTTPSConnection(domain, addresses[0]) as connection:
            connection.request("GET", f"/t/{topic_id}.json", headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                raise ValueError(f"Discussion host returned HTTP {response.status}")
            content_length = response.getheader("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise ValueError("Discussion response exceeds the 2 MB limit")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("Discussion response exceeds the 2 MB limit")
            return json.loads(body.decode("utf-8"))

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
