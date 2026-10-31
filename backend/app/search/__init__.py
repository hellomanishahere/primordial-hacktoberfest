"""Search module exports (Module 9)."""

from app.search.schemas import SearchFilters, SearchHit, SearchResult
from app.search.filters import build_filter_clauses
from app.search.service import SearchService

__all__ = [
    "SearchFilters",
    "SearchHit",
    "SearchResult",
    "build_filter_clauses",
    "SearchService",
]

