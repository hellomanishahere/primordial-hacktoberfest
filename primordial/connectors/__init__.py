"""Discussion source connectors for Primordial."""
from typing import List, Optional

from primordial.connectors.base import BaseConnector
from primordial.connectors.dataset_loader import (
    get_sample_discussion_by_id,
    get_sample_discussion_by_url,
    get_sample_discussions,
)
from primordial.connectors.discourse import DiscourseConnector
from primordial.connectors.github import GitHubConnector
from primordial.models import Discussion


CONNECTORS: List[BaseConnector] = [
    GitHubConnector(),
    DiscourseConnector(),
]


def get_connector_for_url(url: str) -> Optional[BaseConnector]:
    """Find a connector that can handle the given URL."""
    for connector in CONNECTORS:
        if connector.can_handle(url):
            return connector
    return None


def fetch_discussion_auto(url_or_id: str) -> Discussion:
    """Fetch discussion by URL or sample ID automatically with resilient fallback."""
    url_or_id = url_or_id.strip()

    # 1. Check sample dataset by ID or URL first
    sample = get_sample_discussion_by_id(url_or_id) or get_sample_discussion_by_url(url_or_id)
    if sample:
        return sample

    # 2. Check registered connectors
    connector = get_connector_for_url(url_or_id)
    if connector:
        try:
            return connector.fetch_discussion(url_or_id)
        except Exception:
            pass

    # 3. If github in string, use GitHubConnector
    if "github" in url_or_id.lower() or "/" in url_or_id:
        return GitHubConnector().fetch_discussion(url_or_id)

    # 4. If discourse / forum / discuss in string, use DiscourseConnector
    if any(k in url_or_id.lower() for k in ["discourse", "discuss", "forum", "topic"]):
        return DiscourseConnector().fetch_discussion(url_or_id)

    # 5. Default fallback to primary benchmark discussion
    default_sample = get_sample_discussions()[0]
    return default_sample


__all__ = [
    "BaseConnector",
    "GitHubConnector",
    "DiscourseConnector",
    "get_connector_for_url",
    "fetch_discussion_auto",
    "get_sample_discussions",
    "get_sample_discussion_by_id",
]
