"""Database schema definition and migrations (Module 9)."""

import sqlite3
from app.core.logging import get_logger

logger = get_logger("storage.migrations")

SCHEMA_SQL = """
-- Repositories
CREATE TABLE IF NOT EXISTS repositories (
    repository TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingested Discussions
CREATE TABLE IF NOT EXISTS discussions (
    id TEXT PRIMARY KEY,
    repository TEXT NOT NULL,
    entity_number INTEGER NOT NULL,
    resource_type TEXT NOT NULL,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    author TEXT NOT NULL,
    html_url TEXT NOT NULL,
    body TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(repository) REFERENCES repositories(repository) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_discussions_repo ON discussions(repository);
CREATE INDEX IF NOT EXISTS idx_discussions_number ON discussions(entity_number);

-- Discussion Comments
CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    discussion_id TEXT NOT NULL,
    author TEXT NOT NULL,
    author_association TEXT,
    body TEXT NOT NULL,
    html_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comments_disc ON comments(discussion_id);

-- Engineering Decisions
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    discussion_id TEXT NOT NULL,
    decision_summary TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_decisions_disc ON decisions(discussion_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);

-- Rationale & Argument Claims
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_status TEXT NOT NULL,
    supporting_comment_ids TEXT,
    FOREIGN KEY(decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_claims_dec ON claims(decision_id);

-- Rejected Alternatives
CREATE TABLE IF NOT EXISTS alternatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    title TEXT NOT NULL,
    rejection_reason TEXT NOT NULL,
    confidence REAL NOT NULL,
    verification_status TEXT NOT NULL,
    supporting_comment_ids TEXT,
    FOREIGN KEY(decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_alternatives_dec ON alternatives(decision_id);

-- Evidence Verifications
CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    status TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    supporting_comment_ids TEXT,
    contradicting_comment_ids TEXT,
    explanation TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY(decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_verifications_dec ON verifications(decision_id);

-- Architecture Decision Records
CREATE TABLE IF NOT EXISTS adrs (
    adr_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    discussion_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    date TEXT NOT NULL,
    context TEXT,
    problem_statement TEXT,
    decision TEXT NOT NULL,
    file_slug TEXT NOT NULL,
    markdown_content TEXT NOT NULL,
    json_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE,
    FOREIGN KEY(discussion_id) REFERENCES discussions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_adrs_disc ON adrs(discussion_id);
CREATE INDEX IF NOT EXISTS idx_adrs_dec ON adrs(decision_id);
"""

FTS5_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    decision_id UNINDEXED,
    title,
    summary,
    decision,
    rationale,
    alternatives,
    adr_content
);
"""


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Applies schema migrations and full-text index initialization."""
    conn.executescript(SCHEMA_SQL)
    try:
        conn.executescript(FTS5_SQL)
        logger.debug("SQLite FTS5 virtual table verified.")
    except sqlite3.OperationalError as exc:
        logger.warning("FTS5 table setup warning (fallback will be used): %s", exc)
