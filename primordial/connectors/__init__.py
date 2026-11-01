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
    """Fetch an exact sample or a supported public discussion URL."""
    url_or_id = url_or_id.strip()
    if not url_or_id:
        raise ValueError("A discussion URL or sample ID is required")

    # 1. Check sample dataset by ID or URL first
    sample = get_sample_discussion_by_id(url_or_id) or get_sample_discussion_by_url(url_or_id)
    if sample:
        return sample

    # Live fetch failures must be visible to the caller; never replace a source
    # with an unrelated curated discussion.
    connector = get_connector_for_url(url_or_id)
    if connector is None:
        raise ValueError(f"Unsupported discussion source: {url_or_id}")
    return connector.fetch_discussion(url_or_id)


__all__ = [
    "BaseConnector",
    "GitHubConnector",
    "DiscourseConnector",
    "get_connector_for_url",
    "fetch_discussion_auto",
    "get_sample_discussions",
    "get_sample_discussion_by_id",
]
