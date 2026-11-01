"""Historical PR Radar API endpoints (Module 10)."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.exceptions import InvalidGitHubURLException, PrimordialException
from app.core.logging import get_logger
from app.pr_radar.analyzer import PullRequestAnalyzer
from app.pr_radar.matcher import HistoricalDecisionMatcher
from app.pr_radar.reporter import generate_radar_report
from app.pr_radar.schemas import RadarReport
from app.storage.database import init_db

logger = get_logger("api.radar")
router = APIRouter()


class RadarAnalyzeRequest(BaseModel):
    """Payload to analyze a Pull Request with Historical PR Radar."""

    url: str = Field(..., description="Public GitHub Pull Request URL")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevance matching threshold")


@router.post(
    "/analyze",
    response_model=RadarReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze Pull Request for Historical Conflicts & Decisions",
    description="Inspects a GitHub Pull Request and warns about potential conflicts, repeated decisions, or rejected alternatives.",
)
async def analyze_pull_request(payload: RadarAnalyzeRequest) -> RadarReport:
    """Analyzes a Pull Request and correlates against persisted historical decisions."""
    init_db()
    analyzer = PullRequestAnalyzer()
    try:
        pr_info = await analyzer.analyze_url(payload.url)
    except InvalidGitHubURLException as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    except PrimordialException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    matcher = HistoricalDecisionMatcher()
    matches = matcher.match(pr_info, threshold=payload.threshold)
    report = generate_radar_report(pr_info, matches)
    return report

