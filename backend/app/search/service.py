"""Full-text and metadata search service for historical engineering decisions (Module 9)."""

import sqlite3
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.search.filters import build_filter_clauses
from app.search.schemas import SearchFilters, SearchHit, SearchResult
from app.storage.database import get_db_session, resolve_db_path

logger = get_logger("search.service")


class SearchService:
    """Provides indexed full-text and filtered historical decision discovery."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = resolve_db_path(db_path)

    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResult:
        """
        Searches decisions matching query and filters.
        Employs SQLite FTS5 with automatic fallback to LIKE-based pattern search.
        """
        active_filters = filters or SearchFilters()
        q_clean = query.strip()

        with get_db_session(self.db_path) as conn:
            # 1. Attempt FTS5 Full-Text Search if query is provided
            hits: List[SearchHit] = []
            if q_clean:
                try:
                    hits = self._search_fts5(conn, q_clean, active_filters)
                except sqlite3.OperationalError as exc:
                    logger.debug("FTS5 query failed or unavailable, falling back to LIKE: %s", exc)
                    hits = self._search_like_fallback(conn, q_clean, active_filters)
            else:
                # Empty query -> filter-only search
                hits = self._search_like_fallback(conn, "", active_filters)

            return SearchResult(
                query=query,
                total_hits=len(hits),
                hits=hits,
                applied_filters=active_filters.model_dump(),
            )

    def _search_fts5(
        self,
        conn: sqlite3.Connection,
        query: str,
        filters: SearchFilters,
    ) -> List[SearchHit]:
        """Executes full-text match using SQLite FTS5."""
        filter_clause, filter_params = build_filter_clauses(filters)

        # Sanitize query for FTS5 (escape quotes)
        safe_query = f'"{query.replace('"', '""')}"'

        sql = f"""
            SELECT d.decision_id, d.decision_summary, d.status, d.confidence,
                   disc.repository, disc.entity_number, disc.html_url,
                   a.adr_id, a.title as adr_title,
                   snippet(decisions_fts, 6, '<b>', '</b>', '...', 20) as match_snippet
            FROM decisions_fts
            JOIN decisions d ON decisions_fts.decision_id = d.decision_id
            JOIN discussions disc ON d.discussion_id = disc.id
            LEFT JOIN adrs a ON d.decision_id = a.decision_id
            WHERE decisions_fts MATCH ? AND {filter_clause}
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        params = [safe_query] + filter_params + [filters.limit, filters.offset]
        cur = conn.execute(sql, tuple(params))
        rows = cur.fetchall()

        return [
            SearchHit(
                decision_id=r["decision_id"],
                title=r["adr_title"] or r["decision_summary"],
                summary=r["decision_summary"],
                repository=r["repository"],
                entity_number=r["entity_number"],
                status=r["status"],
                adr_id=r["adr_id"],
                source_url=r["html_url"],
                match_snippet=r["match_snippet"],
                confidence=r["confidence"],
            )
            for r in rows
        ]

    def _search_like_fallback(
        self,
        conn: sqlite3.Connection,
        query: str,
        filters: SearchFilters,
    ) -> List[SearchHit]:
        """Robust LIKE-based search fallback for exact keyword and multi-term matches."""
        filter_clause, filter_params = build_filter_clauses(filters)

        where_clauses = [filter_clause]
        params: List[Any] = list(filter_params)

        if query:
            like_pat = f"%{query}%"
            where_clauses.append("""
                (
                    d.decision_summary LIKE ?
                    OR disc.title LIKE ?
                    OR a.title LIKE ?
                    OR a.markdown_content LIKE ?
                    OR d.decision_id IN (
                        SELECT c.decision_id FROM claims c WHERE c.statement LIKE ?
                    )
                    OR d.decision_id IN (
                        SELECT alt.decision_id FROM alternatives alt WHERE alt.title LIKE ? OR alt.rejection_reason LIKE ?
                    )
                )
            """)
            params.extend([like_pat, like_pat, like_pat, like_pat, like_pat, like_pat, like_pat])

        combined_where = " AND ".join(where_clauses)

        sql = f"""
            SELECT d.decision_id, d.decision_summary, d.status, d.confidence,
                   disc.repository, disc.entity_number, disc.html_url,
                   a.adr_id, a.title as adr_title
            FROM decisions d
            JOIN discussions disc ON d.discussion_id = disc.id
            LEFT JOIN adrs a ON d.decision_id = a.decision_id
            WHERE {combined_where}
            ORDER BY d.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([filters.limit, filters.offset])
        cur = conn.execute(sql, tuple(params))
        rows = cur.fetchall()

        return [
            SearchHit(
                decision_id=r["decision_id"],
                title=r["adr_title"] or r["decision_summary"],
                summary=r["decision_summary"],
                repository=r["repository"],
                entity_number=r["entity_number"],
                status=r["status"],
                adr_id=r["adr_id"],
                source_url=r["html_url"],
                match_snippet=f"Match on query '{query}'" if query else None,
                confidence=r["confidence"],
            )
            for r in rows
        ]

