"""Integration tests for Historical PR Radar CLI and FastAPI endpoints (Module 10)."""

import json
from unittest.mock import AsyncMock, patch
import httpx
from httpx import ASGITransport, AsyncClient
import pytest

from app.cli import radar_pr_url
from app.main import app
from app.pr_radar.schemas import ChangedFile, PullRequestAnalysis
from app.storage.database import init_db
from app.storage.repository import StorageRepository
from tests.unit.test_storage_search import (
    make_test_thread,
    make_test_verification_result,
)
from app.adr_generation.generator import ADRGenerator


@pytest.fixture
def seeded_db(tmp_path):
    db_file = str(tmp_path / "radar_integration.db")
    init_db(db_file)
    repo = StorageRepository(db_file)
    thread = make_test_thread(repo="nodejs/node", entity_number=41749)
    v_res = make_test_verification_result(repo="nodejs/node", entity_number=41749)
    adr_res = ADRGenerator().generate(thread, v_res)
    repo.save_pipeline_result(thread, v_res, adr_res)
    return db_file


@pytest.fixture
def mock_pr_analysis():
    return PullRequestAnalysis(
        repository="nodejs/node",
        pr_number=50001,
        title="Re-add node-fetch userland wrapper",
        url="https://github.com/nodejs/node/pull/50001",
        author="contributor",
        description="We should re-evaluate node-fetch.",
        changed_files=[
            ChangedFile(filename="lib/fetch.js", status="modified", additions=50, deletions=10)
        ],
    )


@pytest.mark.asyncio
async def test_cli_radar_stdout(capsys, seeded_db, mock_pr_analysis):
    """Verify CLI radar writes formatted radar report to stdout."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"), \
         patch("app.cli.PullRequestAnalyzer.analyze_url", new_callable=AsyncMock) as mock_analyze:

        mock_analyze.return_value = mock_pr_analysis
        await radar_pr_url("https://github.com/nodejs/node/pull/50001")

    captured = capsys.readouterr()
    assert "HISTORICAL PR RADAR REPORT" in captured.out
    assert "Target PR:     #50001" in captured.out
    assert "PREVIOUSLY_REJECTED_APPROACH" in captured.out
    assert "node-fetch" in captured.out


@pytest.mark.asyncio
async def test_cli_radar_file_output(tmp_path, seeded_db, mock_pr_analysis):
    """Verify CLI radar saves report JSON to output path."""
    out_file = tmp_path / "radar_report.json"

    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"), \
         patch("app.cli.PullRequestAnalyzer.analyze_url", new_callable=AsyncMock) as mock_analyze:

        mock_analyze.return_value = mock_pr_analysis
        await radar_pr_url(
            "https://github.com/nodejs/node/pull/50001",
            output_path=str(out_file),
        )

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["has_relevant_decisions"] is True
    assert data["pr_info"]["pr_number"] == 50001
    assert data["previously_rejected_count"] == 1


@pytest.mark.asyncio
async def test_api_radar_analyze_v1(seeded_db, mock_pr_analysis):
    """Verify POST /api/v1/radar/analyze returns structured report."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"), \
         patch("app.api.endpoints.radar.PullRequestAnalyzer.analyze_url", new_callable=AsyncMock) as mock_analyze:

        mock_analyze.return_value = mock_pr_analysis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/radar/analyze",
                json={"url": "https://github.com/nodejs/node/pull/50001", "threshold": 0.4},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["has_relevant_decisions"] is True
        assert len(data["historical_matches"]) >= 1
        assert data["historical_matches"][0]["category"] == "previously_rejected_approach"


@pytest.mark.asyncio
async def test_api_radar_analyze_direct_route(seeded_db, mock_pr_analysis):
    """Verify POST /api/radar/analyze endpoint works."""
    with patch("app.core.config.settings.DATABASE_URL", f"sqlite:///{seeded_db}"), \
         patch("app.api.endpoints.radar.PullRequestAnalyzer.analyze_url", new_callable=AsyncMock) as mock_analyze:

        mock_analyze.return_value = mock_pr_analysis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/radar/analyze",
                json={"url": "https://github.com/nodejs/node/pull/50001"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["pr_info"]["repository"] == "nodejs/node"


@pytest.mark.asyncio
async def test_api_radar_invalid_url_error():
    """Verify invalid URL returns 422 Unprocessable Entity."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/radar/analyze",
            json={"url": "https://notgithub.com/bad/url"},
        )
    assert resp.status_code in (400, 422)
