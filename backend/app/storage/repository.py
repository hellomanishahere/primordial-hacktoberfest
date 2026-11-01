"""Repository for persisting and retrieving Primordial decision records (Module 9)."""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from app.adr_generation.schemas import ADRGenerationResult
from app.core.logging import get_logger
from app.evidence_verification.schemas import EvidenceVerificationResult
from app.preprocessing.schemas import CleanedDiscussionThread
from app.rationale_extraction.schemas import RationaleExtractionResult
from app.storage.database import get_db_session, resolve_db_path

logger = get_logger("storage.repository")


class StorageRepository:
    """Provides high-level transactional storage operations for Primordial."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = resolve_db_path(db_path)

    def save_pipeline_result(
        self,
        thread: CleanedDiscussionThread,
        verification_result: Optional[EvidenceVerificationResult] = None,
        adr_result: Optional[ADRGenerationResult] = None,
        rationale_result: Optional[RationaleExtractionResult] = None,
    ) -> Dict[str, Any]:
        """
        Atomically persists the complete pipeline results into SQLite.
        Updates previously ingested discussions idempotently.
        """
        disc_id = f"{thread.repository}#{thread.entity_number}"

        with get_db_session(self.db_path) as conn:
            # 1. Upsert Repository
            owner, name = thread.repository_owner, thread.repository_name
            conn.execute(
                """
                INSERT INTO repositories (repository, owner, name, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(repository) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
                """,
                (thread.repository, owner, name),
            )

            # 2. Upsert Discussion
            conn.execute(
                """
                INSERT INTO discussions (
                    id, repository, entity_number, resource_type, title,
                    state, author, html_url, body, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    state = excluded.state,
                    body = excluded.body,
                    updated_at = excluded.updated_at
                """,
                (
                    disc_id,
                    thread.repository,
                    thread.entity_number,
                    thread.resource_type,
                    thread.title,
                    thread.state,
                    thread.author,
                    thread.html_url,
                    thread.body,
                    thread.created_at.isoformat(),
                    thread.updated_at.isoformat(),
                ),
            )

            # 3. Upsert Comments
            for c in thread.comments:
                conn.execute(
                    """
                    INSERT INTO comments (
                        comment_id, discussion_id, author, author_association,
                        body, html_url, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(comment_id) DO UPDATE SET
                        body = excluded.body,
                        author_association = excluded.author_association
                    """,
                    (
                        c.id,
                        disc_id,
                        c.author,
                        c.author_association,
                        c.body,
                        c.html_url,
                        c.created_at.isoformat(),
                    ),
                )

            # 4. Save Decisions, Claims, and ADRs
            saved_decisions_count = 0
            if verification_result and verification_result.verified_decisions:
                # Build map of rationale if available
                rat_map = {}
                if rationale_result and rationale_result.rationales:
                    rat_map = {r.decision_id: r for r in rationale_result.rationales}

                adr_map = {}
                if adr_result and adr_result.adrs:
                    # Map ADRs by decision_id or index
                    for adr in adr_result.adrs:
                        adr_map[adr.file_slug] = adr

                for vdec in verification_result.verified_decisions:
                    # Upsert decision
                    conn.execute(
                        """
                        INSERT INTO decisions (
                            decision_id, discussion_id, decision_summary,
                            status, confidence, model_name
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(decision_id) DO UPDATE SET
                            decision_summary = excluded.decision_summary,
                            status = excluded.status,
                            confidence = excluded.confidence
                        """,
                        (
                            vdec.decision_id,
                            disc_id,
                            vdec.decision_summary,
                            vdec.candidate_status,
                            vdec.confidence,
                            verification_result.model_name or "qwen2.5:7b",
                        ),
                    )

                    # Delete previous claims/verifications for this decision to prevent duplicate accumulation
                    conn.execute("DELETE FROM claims WHERE decision_id = ?", (vdec.decision_id,))
                    conn.execute("DELETE FROM alternatives WHERE decision_id = ?", (vdec.decision_id,))
                    conn.execute("DELETE FROM verifications WHERE decision_id = ?", (vdec.decision_id,))

                    # Save claims and verifications
                    for claim in vdec.claim_verifications:
                        conn.execute(
                            """
                            INSERT INTO verifications (
                                decision_id, claim_id, claim_type, claim_text,
                                status, evidence_type, supporting_comment_ids,
                                contradicting_comment_ids, explanation, confidence
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                vdec.decision_id,
                                claim.claim_id,
                                claim.claim_type,
                                claim.claim_text,
                                claim.status.value,
                                claim.evidence_type.value,
                                json.dumps(claim.supporting_comment_ids),
                                json.dumps(claim.contradicting_comment_ids),
                                claim.explanation,
                                claim.confidence,
                            ),
                        )

                        # Also save to claims
                        conn.execute(
                            """
                            INSERT INTO claims (
                                decision_id, claim_type, statement,
                                confidence, evidence_status, supporting_comment_ids
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                vdec.decision_id,
                                claim.claim_type,
                                claim.claim_text,
                                claim.confidence,
                                claim.status.value,
                                json.dumps(claim.supporting_comment_ids),
                            ),
                        )

                        if claim.claim_type == "rejected_alternative":
                            conn.execute(
                                """
                                INSERT INTO alternatives (
                                    decision_id, title, rejection_reason,
                                    confidence, verification_status, supporting_comment_ids
                                )
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    vdec.decision_id,
                                    claim.claim_text,
                                    claim.explanation,
                                    claim.confidence,
                                    claim.status.value,
                                    json.dumps(claim.supporting_comment_ids),
                                ),
                            )

                    saved_decisions_count += 1

            # 5. Save ADR records & update FTS
            if adr_result and adr_result.adrs:
                for adr in adr_result.adrs:
                    from app.adr_generation.templates import render_madr_markdown
                    md_text = render_madr_markdown(adr)
                    json_text = json.dumps(adr.to_dict())

                    # Match decision_id from adr
                    dec_id = None
                    cur = conn.execute("SELECT decision_id FROM decisions WHERE discussion_id = ? LIMIT 1", (disc_id,))
                    row = cur.fetchone()
                    if row:
                        dec_id = row["decision_id"]
                    else:
                        dec_id = f"dec-{thread.entity_number}-1"

                    conn.execute(
                        """
                        INSERT INTO adrs (
                            adr_id, decision_id, discussion_id, title, status,
                            date, context, problem_statement, decision,
                            file_slug, markdown_content, json_content
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(adr_id) DO UPDATE SET
                            title = excluded.title,
                            status = excluded.status,
                            markdown_content = excluded.markdown_content,
                            json_content = excluded.json_content
                        """,
                        (
                            adr.adr_id,
                            dec_id,
                            disc_id,
                            adr.title,
                            adr.status.value,
                            adr.date,
                            adr.context,
                            adr.problem_statement,
                            adr.decision,
                            adr.file_slug,
                            md_text,
                            json_text,
                        ),
                    )

                    # Update FTS5 index
                    try:
                        conn.execute("DELETE FROM decisions_fts WHERE decision_id = ?", (dec_id,))
                        alts_text = " ".join(alt.title + " " + alt.rejection_reason for alt in adr.considered_alternatives)
                        conn.execute(
                            """
                            INSERT INTO decisions_fts (
                                decision_id, title, summary, decision,
                                rationale, alternatives, adr_content
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                dec_id,
                                adr.title,
                                adr.decision,
                                adr.decision,
                                " ".join(adr.decision_drivers),
                                alts_text,
                                md_text,
                            ),
                        )
                    except sqlite3.OperationalError:
                        pass

        logger.info("Persisted discussion %s with %d decision(s).", disc_id, saved_decisions_count)
        return {
            "discussion_id": disc_id,
            "repository": thread.repository,
            "entity_number": thread.entity_number,
            "saved_decisions_count": saved_decisions_count,
        }

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a full decision record with associated discussion, claims, and ADR."""
        with get_db_session(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT d.*, disc.repository, disc.entity_number, disc.title as discussion_title, disc.html_url
                FROM decisions d
                JOIN discussions disc ON d.discussion_id = disc.id
                WHERE d.decision_id = ?
                """,
                (decision_id,),
            )
            dec_row = cur.fetchone()
            if not dec_row:
                return None

            # Fetch claims
            cur = conn.execute(
                "SELECT * FROM claims WHERE decision_id = ?", (decision_id,)
            )
            claims = [dict(r) for r in cur.fetchall()]

            # Fetch alternatives
            cur = conn.execute(
                "SELECT * FROM alternatives WHERE decision_id = ?", (decision_id,)
            )
            alts = [dict(r) for r in cur.fetchall()]

            # Fetch verifications
            cur = conn.execute(
                "SELECT * FROM verifications WHERE decision_id = ?", (decision_id,)
            )
            verifs = [dict(r) for r in cur.fetchall()]

            # Fetch ADR
            cur = conn.execute(
                "SELECT * FROM adrs WHERE decision_id = ?", (decision_id,)
            )
            adr_row = cur.fetchone()
            adr_data = dict(adr_row) if adr_row else None

            res = dict(dec_row)
            res["claims"] = claims
            res["alternatives"] = alts
            res["verifications"] = verifs
            res["adr"] = adr_data
            return res

    def list_decisions(
        self,
        repository: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Lists decisions with optional repository and status filtering."""
        with get_db_session(self.db_path) as conn:
            query = """
                SELECT d.decision_id, d.decision_summary, d.status, d.confidence,
                       disc.repository, disc.entity_number, disc.html_url,
                       a.adr_id
                FROM decisions d
                JOIN discussions disc ON d.discussion_id = disc.id
                LEFT JOIN adrs a ON d.decision_id = a.decision_id
                WHERE 1=1
            """
            params: List[Any] = []
            if repository:
                query += " AND disc.repository = ?"
                params.append(repository)
            if status:
                query += " AND d.status = ?"
                params.append(status)

            query += " ORDER BY d.created_at DESC LIMIT ?"
            params.append(limit)

            cur = conn.execute(query, tuple(params))
            return [dict(r) for r in cur.fetchall()]

    def get_adr(self, adr_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an ADR document by ADR ID."""
        with get_db_session(self.db_path) as conn:
            cur = conn.execute("SELECT * FROM adrs WHERE adr_id = ?", (adr_id,))
            row = cur.fetchone()
            return dict(row) if row else None

