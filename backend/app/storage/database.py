"""SQLite database connection and session management with WAL mode (Module 9)."""

from contextlib import contextmanager
import os
import sqlite3
from typing import Generator, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.storage.migrations import apply_migrations

logger = get_logger("storage.database")


def resolve_db_path(url_or_path: Optional[str] = None) -> str:
    """Parses database URL (e.g. sqlite:///./primordial.db or plain path) to local file path."""
    target = url_or_path or settings.DATABASE_URL
    if target.startswith("sqlite:///"):
        path = target.replace("sqlite:///", "", 1)
    elif target.startswith("sqlite://"):
        path = target.replace("sqlite://", "", 1)
    else:
        path = target

    return os.path.abspath(path)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates an optimized SQLite connection configured with WAL mode and foreign key enforcement.
    """
    path = resolve_db_path(db_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Enforce SQLite WAL mode and foreign keys
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")

    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes database schema and ensures all migrations and FTS tables exist."""
    path = resolve_db_path(db_path)
    conn = get_connection(path)
    try:
        apply_migrations(conn)
        conn.commit()
        logger.info("Initialized Primordial database at: %s", path)
    finally:
        conn.close()


@contextmanager
def get_db_session(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database operations with automatic transaction rollback on error."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise
    finally:
        conn.close()

