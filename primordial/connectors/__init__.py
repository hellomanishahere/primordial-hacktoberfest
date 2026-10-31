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
    """Fetch an exact fixture or a live public discussion; never fabricate source data."""
    url_or_id = url_or_id.strip()

    # 1. Check sample dataset by ID or URL first
    sample = get_sample_discussion_by_id(url_or_id) or get_sample_discussion_by_url(url_or_id)
    if sample:
        return sample

    # 2. Check registered connectors. Propagate fetch errors so callers know
    #    the source could not be retrieved; do not substitute unrelated data.
    connector = get_connector_for_url(url_or_id)
    if connector:
        return connector.fetch_discussion(url_or_id)

    raise ValueError("Enter a supported GitHub issue/pull request or Discourse topic URL, or an exact sample ID")


__all__ = [
    "BaseConnector",
    "GitHubConnector",
    "DiscourseConnector",
    "get_connector_for_url",
    "fetch_discussion_auto",
    "get_sample_discussions",
    "get_sample_discussion_by_id",
]
