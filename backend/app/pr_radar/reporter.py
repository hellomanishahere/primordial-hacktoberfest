"""Developer report generation for Historical PR Radar (Module 10)."""

from typing import List
from app.pr_radar.schemas import HistoricalMatch, MatchCategory, PullRequestAnalysis, RadarReport


def generate_radar_report(
    pr_info: PullRequestAnalysis,
    matches: List[HistoricalMatch],
) -> RadarReport:
    """
    Generates a structured developer recommendations report from historical decision matches.
    """
    conflicts = [m for m in matches if m.category == MatchCategory.POTENTIAL_CONFLICT]
    rejected = [m for m in matches if m.category == MatchCategory.PREVIOUSLY_REJECTED_APPROACH]
    related = [m for m in matches if m.category in (MatchCategory.RELATED_DECISION, MatchCategory.POTENTIALLY_REPEATED_DECISION)]

    recommendations: List[str] = []

    if rejected:
        for m in rejected:
            adr_ref = f" ({m.adr_id})" if m.adr_id else ""
            recommendations.append(
                f"⚠️ Review prior rejected alternative: PR touches an approach previously dismissed in {m.decision_id}{adr_ref}. "
                f"Ensure the reasons for prior rejection are accounted for."
            )

    if conflicts:
        for m in conflicts:
            adr_ref = f" ({m.adr_id})" if m.adr_id else ""
            recommendations.append(
                f"🚨 Potential architectural conflict detected with {m.decision_id}{adr_ref}: "
                f"Verify that modifications do not break architectural invariants established in '{m.decision_summary}'."
            )

    if related:
        for m in related:
            adr_ref = f" ({m.adr_id})" if m.adr_id else ""
            recommendations.append(
                f"ℹ️ Consult historical context in {m.decision_id}{adr_ref} to ensure consistency with prior decisions."
            )

    if not matches:
        recommendations.append(
            "✅ No relevant historical architectural decisions or conflicting decisions detected for this PR."
        )

    return RadarReport(
        pr_info=pr_info,
        historical_matches=matches,
        potential_conflicts_count=len(conflicts),
        previously_rejected_count=len(rejected),
        recommendations=recommendations,
        has_relevant_decisions=len(matches) > 0,
    )

