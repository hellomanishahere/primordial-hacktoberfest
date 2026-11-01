"""Historical decision matching and conflict detection engine (Module 10)."""

import re
from typing import Any, Dict, List, Optional, Set

from app.core.logging import get_logger
from app.pr_radar.schemas import HistoricalMatch, MatchCategory, PullRequestAnalysis
from app.storage.database import get_db_session, resolve_db_path

logger = get_logger("pr_radar.matcher")

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "this", "that", "these", "those", "we", "they", "it",
    "which", "what", "as", "if", "not", "no", "can", "will", "would", "should"
}


def extract_technical_terms(text: str) -> Set[str]:
    """Extracts alphanumeric technical terms from text."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


class HistoricalDecisionMatcher:
    """Matches an incoming Pull Request against persisted historical decisions in SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = resolve_db_path(db_path)

    def match(
        self,
        pr: PullRequestAnalysis,
        threshold: float = 0.5,
    ) -> List[HistoricalMatch]:
        """
        Scans persisted decisions in the local repository database to find related decisions,
        previously rejected approaches, or potential conflicts.
        """
        pr_text = f"{pr.title} {pr.description}"
        pr_tokens = extract_technical_terms(pr_text)
        file_tokens: Set[str] = set()
        for f in pr.changed_files:
            file_tokens.update(extract_technical_terms(f.filename))

        matches: List[HistoricalMatch] = []

        with get_db_session(self.db_path) as conn:
            # Query all historical decisions for this repository
            cur = conn.execute(
                """
                SELECT d.decision_id, d.decision_summary, d.status, d.confidence,
                       disc.id as discussion_id, disc.entity_number, disc.html_url,
                       a.adr_id, a.title as adr_title, a.decision as adr_decision,
                       a.markdown_content
                FROM decisions d
                JOIN discussions disc ON d.discussion_id = disc.id
                LEFT JOIN adrs a ON d.decision_id = a.decision_id
                WHERE disc.repository = ? AND disc.entity_number != ?
                """,
                (pr.repository, pr.pr_number),
            )
            dec_rows = cur.fetchall()

            for d in dec_rows:
                dec_id = d["decision_id"]
                dec_summary = d["decision_summary"]
                dec_tokens = extract_technical_terms(dec_summary)

                # Fetch rejected alternatives for this decision
                cur_alts = conn.execute(
                    "SELECT title, rejection_reason FROM alternatives WHERE decision_id = ?",
                    (dec_id,),
                )
                alternatives = cur_alts.fetchall()

                # Fetch verified claims
                cur_claims = conn.execute(
                    "SELECT claim_type, statement FROM claims WHERE decision_id = ?",
                    (dec_id,),
                )
                claims = cur_claims.fetchall()

                # 1. Check if PR reintroduces a PREVIOUSLY_REJECTED_APPROACH
                reintroduced_alt = None
                for alt in alternatives:
                    alt_tokens = extract_technical_terms(alt["title"])
                    if alt_tokens and len(alt_tokens & pr_tokens) >= 1:
                        reintroduced_alt = alt
                        break

                if reintroduced_alt:
                    reason = reintroduced_alt["rejection_reason"] or "Previously evaluated and discarded."
                    matches.append(
                        HistoricalMatch(
                            decision_id=dec_id,
                            adr_id=d["adr_id"],
                            decision_summary=dec_summary,
                            discussion_url=d["html_url"],
                            category=MatchCategory.PREVIOUSLY_REJECTED_APPROACH,
                            relevance_explanation=(
                                f"PR proposes or references '{reintroduced_alt['title']}', which was previously "
                                f"evaluated and rejected in {d['adr_id'] or dec_id}. Reason: {reason}"
                            ),
                            related_changed_files=[f.filename for f in pr.changed_files[:5]],
                            evidence_references=[f"Historical rejection reason: {reason}"],
                            confidence=0.88,
                        )
                    )
                    continue

                # 2. Check for POTENTIAL_CONFLICT or POTENTIALLY_REPEATED_DECISION
                token_overlap = pr_tokens & dec_tokens
                file_overlap = file_tokens & dec_tokens

                # Overlap score calculation
                overlap_score = 0.0
                if dec_tokens:
                    overlap_score = len(token_overlap) / len(dec_tokens)

                if file_overlap:
                    overlap_score = max(overlap_score, 0.6)

                if overlap_score >= threshold:
                    # Check conflict signals
                    is_conflict = any(
                        word in pr_text.lower()
                        for word in ("revert", "replace", "remove", "deprecate", "alternative to", "refactor away")
                    )

                    is_repeated = any(
                        word in pr_text.lower()
                        for word in ("re-implement", "duplicate", "adopt again")
                    )

                    if is_conflict:
                        category = MatchCategory.POTENTIAL_CONFLICT
                        expl = (
                            f"PR may conflict with previously adopted decision '{dec_summary}'. "
                            f"PR proposes modifications touching the same technical scope."
                        )
                    elif is_repeated:
                        category = MatchCategory.POTENTIALLY_REPEATED_DECISION
                        expl = f"PR appears to re-implement or repeat previously established decision '{dec_summary}'."
                    else:
                        category = MatchCategory.RELATED_DECISION
                        expl = (
                            f"PR is technically related to prior decision '{dec_summary}' "
                            f"(shared concepts: {', '.join(list(token_overlap | file_overlap)[:4])})."
                        )

                    matches.append(
                        HistoricalMatch(
                            decision_id=dec_id,
                            adr_id=d["adr_id"],
                            decision_summary=dec_summary,
                            discussion_url=d["html_url"],
                            category=category,
                            relevance_explanation=expl,
                            related_changed_files=[f.filename for f in pr.changed_files[:5]],
                            evidence_references=[f"Shared concepts: {', '.join(list(token_overlap)[:3])}"],
                            confidence=round(min(0.95, max(0.5, overlap_score)), 2),
                        )
                    )

        # Sort matches by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

