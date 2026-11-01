"""Overview statistics and metrics endpoint for dashboard (Module 11)."""

from typing import Any, Dict
from fastapi import APIRouter
from app.storage.database import get_db_session, init_db

router = APIRouter()


@router.get(
    "/overview",
    summary="Dashboard Overview Metrics",
    description="Returns aggregate counts of repositories, discussions, decisions, and ADRs.",
)
async def get_overview_metrics() -> Dict[str, Any]:
    """Computes real-time statistics from SQLite database."""
    init_db()
    with get_db_session() as conn:
        repo_count = conn.execute("SELECT COUNT(*) as c FROM repositories").fetchone()["c"]
        disc_count = conn.execute("SELECT COUNT(*) as c FROM discussions").fetchone()["c"]
        dec_count = conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
        verif_count = conn.execute("SELECT COUNT(*) as c FROM verifications WHERE status = 'verified'").fetchone()["c"]
        adr_count = conn.execute("SELECT COUNT(*) as c FROM adrs").fetchone()["c"]

        # Fetch 5 most recent decisions
        recent_cur = conn.execute(
            """
            SELECT d.decision_id, d.decision_summary, d.status, d.created_at,
                   disc.repository, disc.entity_number, a.adr_id
            FROM decisions d
            JOIN discussions disc ON d.discussion_id = disc.id
            LEFT JOIN adrs a ON d.decision_id = a.decision_id
            ORDER BY d.created_at DESC LIMIT 5
            """
        )
        recent_activity = [dict(r) for r in recent_cur.fetchall()]

    return {
        "repositories_analyzed": repo_count,
        "discussions_processed": disc_count,
        "decisions_detected": dec_count,
        "verified_decisions": verif_count,
        "adrs_generated": adr_count,
        "recent_activity": recent_activity,
    }

