"""Search query models and response schemas (Module 9)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Filter criteria for searching historical decisions."""

    repository: Optional[str] = Field(default=None, description="Exact repository filter, e.g. 'nodejs/node'")
    status: Optional[str] = Field(default=None, description="Decision status: accepted, proposed, rejected, deferred, unclear")
    verification_status: Optional[str] = Field(default=None, description="Verification status: verified, partially_supported, contradicted, unsupported")
    start_date: Optional[str] = Field(default=None, description="ISO start date filter")
    end_date: Optional[str] = Field(default=None, description="ISO end date filter")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class SearchHit(BaseModel):
    """An individual search match pointing to a historical engineering decision."""

    decision_id: str
    title: str
    summary: str
    repository: str
    entity_number: int
    status: str
    adr_id: Optional[str] = None
    verification_status: str = "verified"
    source_url: str
    match_snippet: Optional[str] = None
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class SearchResult(BaseModel):
    """Top-level search result payload."""

    query: str
    total_hits: int
    hits: List[SearchHit]
    applied_filters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_hits": self.total_hits,
            "hits": [h.to_dict() for h in self.hits],
            "applied_filters": self.applied_filters,
        }
