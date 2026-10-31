"""Search query filtering and SQL WHERE clause builders (Module 9)."""

from typing import Any, List, Tuple
from app.search.schemas import SearchFilters


def build_filter_clauses(filters: SearchFilters) -> Tuple[str, List[Any]]:
    """Constructs dynamic WHERE conditions and parameter values from SearchFilters."""
    conditions: List[str] = []
    params: List[Any] = []

    if filters.repository:
        conditions.append("disc.repository = ?")
        params.append(filters.repository.strip())

    if filters.status:
        conditions.append("LOWER(d.status) = LOWER(?)")
        params.append(filters.status.strip())

    if filters.verification_status:
        conditions.append("""
            d.decision_id IN (
                SELECT v.decision_id FROM verifications v
                WHERE LOWER(v.status) = LOWER(?)
            )
        """)
        params.append(filters.verification_status.strip())

    if filters.start_date:
        conditions.append("disc.created_at >= ?")
        params.append(filters.start_date.strip())

    if filters.end_date:
        conditions.append("disc.created_at <= ?")
        params.append(filters.end_date.strip())

    clause_str = " AND ".join(conditions) if conditions else "1=1"
    return clause_str, params
