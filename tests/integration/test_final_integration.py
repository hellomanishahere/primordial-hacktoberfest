"""Module 12: End-to-end integration tests for the full Primordial platform.

Tests cover:
- Complete API endpoint availability and response format
- CORS headers presence
- Empty database states
- Pipeline request validation
- Cross-module data flow verification
- Frontend build artifact existence
- Database schema validation
- CLI subcommand availability
"""

import os
import sqlite3

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.core.config import settings
from app.storage.database import init_db


# ── Temp DB fixture ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path):
    """Redirect all database operations to a temporary SQLite database."""
    db_path = str(tmp_path / "test_integration.db")
    with patch.object(settings, "DATABASE_URL", db_path):
        init_db()
        # Import app AFTER patching so all endpoints use the temp DB
        from app.main import app
        yield app


@pytest.fixture
def client(_use_temp_db):
    """TestClient using the temp-DB-patched app."""
    return TestClient(_use_temp_db)


# ── 1. Root & Health ─────────────────────────────────────────────────────────

class TestCoreEndpoints:
    def test_root_returns_service_metadata(self, client):
        res = client.get("/")
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "Primordial"
        assert "version" in body
        assert "docs_url" in body

    def test_health_endpoint_returns_ok(self, client):
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] in ("ok", "degraded", "healthy")

    def test_nonexistent_route_returns_404(self, client):
        res = client.get("/api/v1/does-not-exist")
        assert res.status_code == 404

    def test_method_not_allowed_returns_405(self, client):
        res = client.delete("/api/v1/health")
        assert res.status_code == 405


# ── 2. CORS ──────────────────────────────────────────────────────────────────

class TestCORS:
    def test_cors_headers_present_on_options(self, client):
        res = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in res.headers

    def test_cors_allows_any_origin(self, client):
        res = client.get(
            "/api/v1/health",
            headers={"Origin": "http://example.com"},
        )
        assert res.headers.get("access-control-allow-origin") in ("*", "http://example.com")


# ── 3. Overview (empty DB) ──────────────────────────────────────────────────

class TestOverviewEmptyDB:
    def test_overview_returns_zero_counts(self, client):
        res = client.get("/api/v1/overview")
        assert res.status_code == 200
        body = res.json()
        assert body["repositories_analyzed"] == 0
        assert body["discussions_processed"] == 0
        assert body["decisions_detected"] == 0
        assert body["verified_decisions"] == 0
        assert body["adrs_generated"] == 0
        assert body["recent_activity"] == []


# ── 4. Decisions (empty DB) ─────────────────────────────────────────────────

class TestDecisionsEmptyDB:
    def test_list_decisions_empty(self, client):
        res = client.get("/api/v1/decisions")
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 0
        assert body["decisions"] == []

    def test_search_decisions_empty(self, client):
        res = client.get("/api/v1/decisions", params={"query": "undici"})
        assert res.status_code == 200

    def test_get_nonexistent_decision(self, client):
        res = client.get("/api/v1/decisions/nonexistent-id")
        assert res.status_code == 404

    def test_get_nonexistent_adr(self, client):
        res = client.get("/api/v1/decisions/nonexistent-id/adr")
        assert res.status_code == 404


# ── 5. Extract Endpoint Validation ──────────────────────────────────────────

class TestExtractValidation:
    def test_extract_rejects_empty_body(self, client):
        res = client.post("/api/v1/extract", json={})
        assert res.status_code == 422

    def test_extract_rejects_invalid_url(self, client):
        res = client.post("/api/v1/extract", json={"url": "not-a-github-url"})
        assert res.status_code == 422

    def test_extract_rejects_missing_url(self, client):
        res = client.post("/api/v1/extract", json={"model": "qwen2.5:7b"})
        assert res.status_code == 422

    def test_extract_rejects_tokens_out_of_range(self, client):
        res = client.post(
            "/api/v1/extract",
            json={"url": "https://github.com/nodejs/node/pull/41749", "max_tokens": 999},
        )
        assert res.status_code == 422


# ── 6. Radar Endpoint Validation ────────────────────────────────────────────

class TestRadarValidation:
    def test_radar_rejects_empty_body(self, client):
        res = client.post("/api/v1/radar/analyze", json={})
        assert res.status_code == 422

    def test_radar_rejects_invalid_url(self, client):
        res = client.post("/api/v1/radar/analyze", json={"url": "not-valid"})
        assert res.status_code == 422

    def test_radar_rejects_threshold_out_of_range(self, client):
        res = client.post(
            "/api/v1/radar/analyze",
            json={"url": "https://github.com/owner/repo/pull/1", "threshold": 5.0},
        )
        assert res.status_code == 422

    def test_radar_legacy_mount_rejects_empty(self, client):
        """Test the direct /api/radar/analyze mount also works."""
        res = client.post("/api/radar/analyze", json={})
        assert res.status_code == 422


# ── 7. Cross-Module Schema Consistency ──────────────────────────────────────

class TestSchemaConsistency:
    """Verify that schemas referenced across modules are importable and compatible."""

    def test_canonical_thread_importable(self):
        from app.domain.entities import CanonicalDiscussionThread, CanonicalDiscussionComment
        assert CanonicalDiscussionThread is not None
        assert CanonicalDiscussionComment is not None

    def test_cleaned_thread_importable(self):
        from app.preprocessing.cleaner import CleanedDiscussionThread
        assert CleanedDiscussionThread is not None

    def test_detection_schemas_importable(self):
        from app.decision_detection.schemas import (
            DecisionDetectionResult,
            CandidateDecision,
        )
        assert DecisionDetectionResult is not None
        assert CandidateDecision is not None

    def test_rationale_schemas_importable(self):
        from app.rationale_extraction.schemas import (
            RationaleExtractionResult,
            ExtractedDecisionRationale,
        )
        assert RationaleExtractionResult is not None
        assert ExtractedDecisionRationale is not None

    def test_verification_schemas_importable(self):
        from app.evidence_verification.schemas import (
            EvidenceVerificationResult,
            ClaimVerificationResult,
        )
        assert EvidenceVerificationResult is not None
        assert ClaimVerificationResult is not None

    def test_adr_schemas_importable(self):
        from app.adr_generation.schemas import ADRGenerationResult, ADRDocument
        assert ADRGenerationResult is not None
        assert ADRDocument is not None

    def test_storage_importable(self):
        from app.storage.database import init_db, get_db_session
        from app.storage.repository import StorageRepository
        assert StorageRepository is not None

    def test_search_importable(self):
        from app.search.service import SearchService
        from app.search.schemas import SearchFilters, SearchResult
        assert SearchService is not None

    def test_radar_schemas_importable(self):
        from app.pr_radar.schemas import (
            RadarReport,
            PullRequestAnalysis,
            HistoricalMatch,
            MatchCategory,
        )
        assert MatchCategory.POTENTIAL_CONFLICT.value == "potential_conflict"


# ── 8. Frontend Build Artifacts ─────────────────────────────────────────────

class TestFrontendBuild:
    """Verify frontend source files exist."""

    FRONTEND_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend"
    )

    def test_package_json_exists(self):
        assert os.path.isfile(os.path.join(self.FRONTEND_DIR, "package.json"))

    def test_tsconfig_exists(self):
        assert os.path.isfile(os.path.join(self.FRONTEND_DIR, "tsconfig.json"))

    def test_vite_config_exists(self):
        assert os.path.isfile(os.path.join(self.FRONTEND_DIR, "vite.config.ts"))

    def test_index_html_exists(self):
        assert os.path.isfile(os.path.join(self.FRONTEND_DIR, "index.html"))

    def test_source_files_exist(self):
        src_dir = os.path.join(self.FRONTEND_DIR, "src")
        assert os.path.isfile(os.path.join(src_dir, "main.tsx"))
        assert os.path.isfile(os.path.join(src_dir, "App.tsx"))
        assert os.path.isfile(os.path.join(src_dir, "index.css"))
        assert os.path.isfile(os.path.join(src_dir, "api", "client.ts"))
        assert os.path.isfile(os.path.join(src_dir, "types", "index.ts"))

    def test_page_components_exist(self):
        pages_dir = os.path.join(self.FRONTEND_DIR, "src", "pages")
        expected = [
            "Overview.tsx", "AnalyzeDiscussion.tsx", "Decisions.tsx",
            "DecisionDetail.tsx", "ADRLibrary.tsx", "ADRView.tsx", "Search.tsx",
            "PRRadar.tsx", "Settings.tsx",
        ]
        for page in expected:
            assert os.path.isfile(os.path.join(pages_dir, page)), f"Missing page: {page}"

    def test_component_files_exist(self):
        comp_dir = os.path.join(self.FRONTEND_DIR, "src", "components")
        expected = [
            "Sidebar.tsx", "StatusBadge.tsx", "LoadingSpinner.tsx",
            "EmptyState.tsx", "ErrorMessage.tsx",
        ]
        for comp in expected:
            assert os.path.isfile(os.path.join(comp_dir, comp)), f"Missing component: {comp}"


# ── 9. Database Schema ──────────────────────────────────────────────────────

class TestDatabaseSchema:
    """Verify the SQLite database schema is correctly initialized."""

    def test_tables_created(self, tmp_path):
        db_path = str(tmp_path / "schema_test.db")
        with patch.object(settings, "DATABASE_URL", db_path):
            init_db()
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

        expected_tables = {"repositories", "discussions", "decisions", "verifications", "adrs"}
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"


# ── 10. CLI Subcommands Availability ────────────────────────────────────────

class TestCLISubcommands:
    """Verify all CLI subcommands are registered and show help."""

    EXPECTED_COMMANDS = [
        "fetch", "preprocess", "detect", "extract-rationale",
        "verify-evidence", "generate-adr", "search", "list-decisions",
        "show-decision", "radar", "extract",
    ]

    def test_cli_help_lists_all_subcommands(self):
        import subprocess
        out = subprocess.check_output(
            [".venv/bin/python", "-m", "app.cli", "--help"],
            env={**os.environ, "PYTHONPATH": "backend"},
        ).decode()
        for cmd_name in self.EXPECTED_COMMANDS:
            assert cmd_name in out, f"CLI subcommand '{cmd_name}' not listed in help"
