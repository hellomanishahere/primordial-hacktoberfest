"""FastAPI endpoints for querying and retrieving persisted decisions and ADRs (Module 9)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.search.schemas import SearchFilters, SearchResult
from app.search.service import SearchService
from app.storage.database import get_db_session, init_db
from app.storage.repository import StorageRepository

router = APIRouter()


@router.get(
    "",
    summary="List and Search Engineering Decisions",
    description="Retrieves persisted historical decisions with optional keyword search and filtering.",
)
async def list_or_search_decisions(
    query: Optional[str] = Query(default=None, description="Keywords or search query"),
    repository: Optional[str] = Query(default=None, description="Filter by repository"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """Lists decisions from database or performs full-text search when query parameter is provided."""
    init_db()
    if query:
        search_svc = SearchService()
        filters = SearchFilters(
            repository=repository,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        res = search_svc.search(query, filters=filters)
        return res.to_dict()

    repo = StorageRepository()
    records = repo.list_decisions(repository=repository, status=status_filter, limit=limit)
    return {
        "total": len(records),
        "decisions": records,
    }


@router.get(
    "/{decision_id}",
    summary="Retrieve Decision Details with Claims & Provenance",
    description="Fetches single decision with full claims, rejected alternatives, verifications, and ADR link.",
)
async def get_decision_details(decision_id: str) -> Dict[str, Any]:
    """Returns single decision record or raises 404."""
    init_db()
    repo = StorageRepository()
    dec = repo.get_decision(decision_id)
    if not dec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' not found.",
        )
    return dec


@router.get(
    "/{decision_id}/adr",
    summary="Retrieve ADR associated with Decision",
    description="Returns markdown and structured JSON of the ADR linked to this decision.",
)
async def get_decision_adr(decision_id: str) -> Dict[str, Any]:
    """Returns ADR associated with decision or raises 404."""
    init_db()
    repo = StorageRepository()
    dec = repo.get_decision(decision_id)
    if not dec or not dec.get("adr"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ADR found for decision '{decision_id}'.",
        )
    return dec["adr"]

