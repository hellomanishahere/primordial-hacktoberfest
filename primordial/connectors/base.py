"""Base connector interface for Primordial."""
from abc import ABC, abstractmethod
from typing import Optional

from primordial.models import Discussion


class BaseConnector(ABC):
    """Abstract base class for discussion source connectors."""

    @abstractmethod
    def can_handle(self, source_url: str) -> bool:
        """Return True if connector can handle the given URL or identifier."""
        pass

    @abstractmethod
    def fetch_discussion(self, source_url: str) -> Discussion:
        """Fetch and normalize discussion into a standard Discussion model."""
        pass
