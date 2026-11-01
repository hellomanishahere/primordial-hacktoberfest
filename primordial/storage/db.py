"""Persistent SQLite storage layer for Decision Library and Discussions."""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from primordial.models import DecisionRecord, Discussion, PipelineStageResult


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "primordial.db"
)


class DecisionStorage:
    """SQLite-backed persistent store for Primordial decisions and discussions."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                # Discussions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS discussions (
                        id TEXT PRIMARY KEY,
                        source_type TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        author TEXT,
                        created_at TEXT,
                        closed_at TEXT,
                        labels_json TEXT,
                        comments_json TEXT,
                        metadata_json TEXT,
                        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Decision records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS decision_records (
                        id TEXT PRIMARY KEY,
                        discussion_id TEXT,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        date TEXT,
                        context TEXT,
                        problem_statement TEXT,
                        decision_outcome TEXT,
                        accepted_option TEXT,
                        considered_options_json TEXT,
                        rejected_alternatives_json TEXT,
                        consequences_positive_json TEXT,
                        consequences_negative_json TEXT,
                        affected_components_json TEXT,
                        evidence_quotes_json TEXT,
                        madr_content TEXT,
                        created_at TEXT,
                        FOREIGN KEY(discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
                    )
                """)

                # Pipeline execution logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discussion_id TEXT,
                        stage_num INTEGER,
                        stage_name TEXT,
                        model_name TEXT,
                        execution_time_ms REAL,
                        output_json TEXT,
                        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        finally:
            conn.close()

    # --- Discussion Operations ---

    def save_discussion(self, discussion: Discussion) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO discussions (
                        id, source_type, source_url, title, description,
                        author, created_at, closed_at, labels_json, comments_json, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        discussion.id,
                        discussion.source_type,
                        discussion.source_url,
                        discussion.title,
                        discussion.description,
                        discussion.author,
                        discussion.created_at,
                        discussion.closed_at,
                        json.dumps(discussion.labels),
                        json.dumps([c.to_dict() for c in discussion.comments]),
                        json.dumps(discussion.metadata),
                    ),
                )
        finally:
            conn.close()

    def get_discussion(self, discussion_id: str) -> Optional[Discussion]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM discussions WHERE id = ?", (discussion_id,)
            ).fetchone()
            if not row:
                return None
            return Discussion(
                id=row["id"],
                source_type=row["source_type"],
                source_url=row["source_url"],
                title=row["title"],
                description=row["description"] or "",
                author=row["author"] or "anonymous",
                created_at=row["created_at"] or "",
                closed_at=row["closed_at"],
                labels=json.loads(row["labels_json"] or "[]"),
                comments=[
                    Discussion.from_dict({"id": "tmp", "comments": json.loads(row["comments_json"] or "[]")}).comments
                ][0]
                if row["comments_json"]
                else [],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
        finally:
            conn.close()

    def list_discussions(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT id, source_type, source_url, title, author, created_at, saved_at FROM discussions ORDER BY saved_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --- Decision Record Operations ---

    def save_decision(self, decision: DecisionRecord) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO decision_records (
                        id, discussion_id, title, status, date,
                        context, problem_statement, decision_outcome, accepted_option,
                        considered_options_json, rejected_alternatives_json,
                        consequences_positive_json, consequences_negative_json,
                        affected_components_json, evidence_quotes_json, madr_content, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decision.id,
                        decision.discussion_id,
                        decision.title,
                        decision.status,
                        decision.date,
                        decision.context,
                        decision.problem_statement,
                        decision.decision_outcome,
                        decision.accepted_option,
                        json.dumps(decision.considered_options),
                        json.dumps([ra.to_dict() for ra in decision.rejected_alternatives]),
                        json.dumps(decision.consequences_positive),
                        json.dumps(decision.consequences_negative),
                        json.dumps(decision.affected_components),
                        json.dumps([eq.to_dict() for eq in decision.evidence_quotes]),
                        decision.madr_content,
                        decision.created_at,
                    ),
                )
        finally:
            conn.close()

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM decision_records WHERE id = ?", (decision_id,)
            ).fetchone()
            if not row:
                return None
            data = {
                "id": row["id"],
                "discussion_id": row["discussion_id"],
                "title": row["title"],
                "status": row["status"],
                "date": row["date"],
                "context": row["context"],
                "problem_statement": row["problem_statement"],
                "decision_outcome": row["decision_outcome"],
                "accepted_option": row["accepted_option"],
                "considered_options": json.loads(row["considered_options_json"] or "[]"),
                "rejected_alternatives": json.loads(row["rejected_alternatives_json"] or "[]"),
                "consequences_positive": json.loads(row["consequences_positive_json"] or "[]"),
                "consequences_negative": json.loads(row["consequences_negative_json"] or "[]"),
                "affected_components": json.loads(row["affected_components_json"] or "[]"),
                "evidence_quotes": json.loads(row["evidence_quotes_json"] or "[]"),
                "madr_content": row["madr_content"] or "",
                "created_at": row["created_at"],
            }
            return DecisionRecord.from_dict(data)
        finally:
            conn.close()

    def list_decisions(self) -> List[DecisionRecord]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM decision_records ORDER BY created_at DESC"
            ).fetchall()
            decisions = []
            for row in rows:
                data = {
                    "id": row["id"],
                    "discussion_id": row["discussion_id"],
                    "title": row["title"],
                    "status": row["status"],
                    "date": row["date"],
                    "context": row["context"],
                    "problem_statement": row["problem_statement"],
                    "decision_outcome": row["decision_outcome"],
                    "accepted_option": row["accepted_option"],
                    "considered_options": json.loads(row["considered_options_json"] or "[]"),
                    "rejected_alternatives": json.loads(row["rejected_alternatives_json"] or "[]"),
                    "consequences_positive": json.loads(row["consequences_positive_json"] or "[]"),
                    "consequences_negative": json.loads(row["consequences_negative_json"] or "[]"),
                    "affected_components": json.loads(row["affected_components_json"] or "[]"),
                    "evidence_quotes": json.loads(row["evidence_quotes_json"] or "[]"),
                    "madr_content": row["madr_content"] or "",
                    "created_at": row["created_at"],
                }
                decisions.append(DecisionRecord.from_dict(data))
            return decisions
        finally:
            conn.close()

    def search_decisions(
        self, query: str = "", status: Optional[str] = None
    ) -> List[DecisionRecord]:
        """Search decision records by query text across title, outcomes, rejected alternatives, and components."""
        all_decisions = self.list_decisions()
        if not query and not status:
            return all_decisions

        q_lower = query.strip().lower()
        results = []

        for d in all_decisions:
            if status and d.status.lower() != status.lower():
                continue

            if not q_lower:
                results.append(d)
                continue

            # Check matches in title, accepted option, context, problem statement
            matched = False
            fields_to_check = [
                d.title,
                d.accepted_option,
                d.decision_outcome,
                d.problem_statement,
                d.context,
                " ".join(d.considered_options),
                " ".join(d.affected_components),
            ]
            for f in fields_to_check:
                if q_lower in f.lower():
                    matched = True
                    break

            if not matched:
                # Check rejected alternatives
                for ra in d.rejected_alternatives:
                    if q_lower in ra.name.lower() or any(
                        q_lower in r.lower() for r in ra.rejection_reasons
                    ):
                        matched = True
                        break

            if matched:
                results.append(d)

        return results

    def save_stage_log(
        self, discussion_id: str, stage_result: PipelineStageResult
    ) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO pipeline_logs (
                        discussion_id, stage_num, stage_name, model_name, execution_time_ms, output_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        discussion_id,
                        stage_result.stage_num,
                        stage_result.stage_name,
                        stage_result.model_name,
                        stage_result.execution_time_ms,
                        json.dumps(stage_result.output),
                    ),
                )
        finally:
            conn.close()
