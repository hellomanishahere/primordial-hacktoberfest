"""Pull Request Historical Decision Radar Engine.

Detects when newly submitted or simulated PRs touch code paths bound to historical decisions
or re-introduce rejected architectural alternatives.
"""
from __future__ import annotations

import fnmatch
import os
import re
from typing import List, Optional

from primordial.models import DecisionRecord, PullRequestDiff, RadarAlert
from primordial.storage.db import DecisionStorage


def match_file_pattern(file_path: str, pattern: str) -> bool:
    """Check if file_path matches a glob pattern or path fragment."""
    file_norm = file_path.strip().replace("\\", "/").lower()
    pattern_norm = pattern.strip().replace("\\", "/").lower()

    # Exact or substring match
    if pattern_norm in file_norm or file_norm in pattern_norm:
        return True

    # Basename match (e.g. config.py matching src/settings/config.py)
    if os.path.basename(file_norm) == os.path.basename(pattern_norm):
        return True

    # Glob match (e.g. crates/uv-settings/*)
    if fnmatch.fnmatch(file_norm, pattern_norm):
        return True

    return False


GENERIC_STOP_WORDS = {
    "configuration", "format", "store", "storage", "engine", "system",
    "backend", "option", "approach", "layer", "support", "module",
    "parser", "architecture", "direct", "native", "legacy", "integration"
}


class PRDecisionRadar:
    """Scans pull requests against the persistent Decision Library."""

    def __init__(self, storage: Optional[DecisionStorage] = None):
        self.storage = storage or DecisionStorage()

    def scan_pull_request(self, pr: PullRequestDiff) -> List[RadarAlert]:
        """Scan a PR diff and changed files against all known historical decisions."""
        decisions = self.storage.list_decisions()
        alerts: List[RadarAlert] = []

        pr_text_corpus = f"{pr.title} {pr.description} {pr.patch_diff}".lower()

        for decision in decisions:
            # 1. Check for file path overlap with affected_components
            matched_files = []
            for cf in pr.changed_files:
                for comp in decision.affected_components:
                    if match_file_pattern(cf, comp):
                        matched_files.append(cf)
                        break

            # 2. Check for Resurrected Rejected Alternatives (Critical / High severity)
            for ra in decision.rejected_alternatives:
                # Key terms of the rejected alternative, excluding generic stop words
                ra_clean = re.sub(r"[^a-zA-Z0-9\s]", " ", ra.name).lower()
                all_tokens = [t for t in ra_clean.split() if len(t) > 2]
                distinctive_tokens = [t for t in all_tokens if t not in GENERIC_STOP_WORDS]

                if not distinctive_tokens:
                    distinctive_tokens = all_tokens

                # Check if any distinctive token or file matches the rejected alternative
                keyword_match = any(token in pr_text_corpus for token in distinctive_tokens)
                file_match = any(token in cf.lower() for cf in pr.changed_files for token in distinctive_tokens)

                if keyword_match or file_match:
                    dec_title_clean = decision.title.split(': ', 1)[-1] if ': ' in decision.title else decision.title
                    reasons_summary = "; ".join(ra.rejection_reasons[:2])
                    alerts.append(
                        RadarAlert(
                            id=f"alert-resurrected-{decision.id}-{ra.name.replace(' ', '_')[:12]}",
                            pr_id=pr.pr_id,
                            severity="high",
                            matched_decision_id=decision.id,
                            matched_decision_title=f"{decision.id}: {dec_title_clean}",
                            conflict_type="resurrected_rejected_alternative",
                            message=(
                                f"⚠️ Caution: PR appears to re-propose or introduce '{ra.name}', "
                                f"which was previously DEBATED AND REJECTED in {decision.id}."
                            ),
                            historical_context=(
                                f"In {decision.id}: {dec_title_clean} (Decided: {decision.date}), "
                                f"the team rejected '{ra.name}' for the following reasons: {reasons_summary}."
                            ),
                            matched_files=matched_files or pr.changed_files,
                            rejected_alternative=ra.name,
                            rejection_reason=reasons_summary,
                            evidence_link=ra.comment_url or f"/decisions/{decision.id}",
                        )
                    )

            # 3. Check for Architectural Component Modification (Medium severity)
            if matched_files and not any(a.matched_decision_id == decision.id for a in alerts):
                alerts.append(
                    RadarAlert(
                        id=f"alert-component-{decision.id}",
                        pr_id=pr.pr_id,
                        severity="medium",
                        matched_decision_id=decision.id,
                        matched_decision_title=decision.title,
                        conflict_type="architectural_deviation",
                        message=(
                            f"ℹ️ Architectural Notice: Modified files ({', '.join(matched_files)}) "
                            f"are governed by {decision.id} ({decision.title})."
                        ),
                        historical_context=(
                            f"This component was designed under decision '{decision.accepted_option}'. "
                            f"Ensure new modifications do not violate the recorded constraints."
                        ),
                        matched_files=matched_files,
                        rejected_alternative=None,
                        rejection_reason=None,
                        evidence_link=f"/decisions/{decision.id}",
                    )
                )

        return alerts
