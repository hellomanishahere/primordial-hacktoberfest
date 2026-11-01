"""Integration tests for Primordial CLI storage and search subcommands."""

from unittest.mock import patch
import pytest

from app.adr_generation.generator import ADRGenerator
from app.cli import list_decisions_cli, search_decisions_cli, show_decision_cli
from app.storage.database import init_db
from app.storage.repository import StorageRepository
from tests.unit.test_storage_search import (
    make_test_thread,
    make_test_verification_result,
)


@pytest.fixture
def seeded_db(tmp_path):
    """Initializes and seeds a temporary SQLite database with a verified decision."""
    db_file = str(tmp_path / "test_cli_primordial.db")
    init_db(db_file)
    repo = StorageRepository(db_file)
    thread = make_test_thread()
    v_res = make_test_verification_result()
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)
    return db_file


def test_cli_search_command_output(capsys, seeded_db):
    """Verify search command prints hits with snippet and metadata."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"):
        search_decisions_cli(query="Undici")

    captured = capsys.readouterr()
    assert "--- Decision Search Results: 'Undici' ---" in captured.out
    assert "Total Matches: 1" in captured.out
    assert "dec-41749-1" in captured.out
    assert "nodejs/node #41749" in captured.out


def test_cli_search_no_matches(capsys, seeded_db):
    """Verify search prints informative message when nothing matches."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"):
        search_decisions_cli(query="NonExistentFrameworkXYZ")

    captured = capsys.readouterr()
    assert "Total Matches: 0" in captured.out
    assert "No historical engineering decisions matched your query." in captured.out


def test_cli_list_decisions_command(capsys, seeded_db):
    """Verify list-decisions prints overview of stored decisions."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"):
        list_decisions_cli()

    captured = capsys.readouterr()
    assert "--- Persisted Engineering Decisions (Total: 1) ---" in captured.out
    assert "dec-41749-1" in captured.out
    assert "nodejs/node #41749" in captured.out


def test_cli_show_decision_command(capsys, seeded_db):
    """Verify show-decision outputs full details, claims, and ADR information."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"):
        show_decision_cli("dec-41749-1")

    captured = capsys.readouterr()
    assert "--- Decision Record: dec-41749-1 ---" in captured.out
    assert "Summary:       Adopt Undici for native Fetch implementation in core" in captured.out
    assert "Status:        ACCEPTED" in captured.out
    assert "Claims & Arguments:" in captured.out
    assert "Rejected Alternatives:" in captured.out
    assert "Associated ADR: ADR-41749-01" in captured.out


def test_cli_show_decision_not_found(capsys, seeded_db):
    """Verify show-decision exits code 1 when decision ID is missing."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"):
        with pytest.raises(SystemExit) as exc_info:
            show_decision_cli("non-existent-id")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Decision 'non-existent-id' not found in database." in captured.err

