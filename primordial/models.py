"""Core data models for Primordial platform."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Participant:
    username: str
    role: str = "contributor"  # author, maintainer, contributor
    avatar_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Comment:
    id: str
    author: str
    created_at: str
    body: str
    url: str
    reply_to_id: Optional[str] = None
    reactions: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Discussion:
    id: str
    source_type: str  # "github" or "discourse"
    source_url: str
    title: str
    description: str
    author: str
    created_at: str
    closed_at: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_messages(self) -> int:
        return 1 + len(self.comments)

    def get_all_participants(self) -> List[str]:
        names = {self.author}
        for c in self.comments:
            if c.author:
                names.add(c.author)
        return sorted(list(names))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "labels": self.labels,
            "comments": [c.to_dict() for c in self.comments],
            "metadata": self.metadata,
            "total_messages": self.total_messages,
            "participants": self.get_all_participants(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Discussion:
        comments = [
            Comment(
                id=c["id"],
                author=c["author"],
                created_at=c.get("created_at", ""),
                body=c.get("body", ""),
                url=c.get("url", ""),
                reply_to_id=c.get("reply_to_id"),
                reactions=c.get("reactions", {}),
            )
            for c in data.get("comments", [])
        ]
        return cls(
            id=data["id"],
            source_type=data.get("source_type", "github"),
            source_url=data.get("source_url", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            author=data.get("author", "anonymous"),
            created_at=data.get("created_at", ""),
            closed_at=data.get("closed_at"),
            labels=data.get("labels", []),
            comments=comments,
            metadata=data.get("metadata", {}),
        )


@dataclass
class Proposal:
    id: str
    name: str
    proposer: str
    description: str
    status: str = "proposed"  # accepted, rejected, superseded, proposed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Argument:
    id: str
    proposal_id: str
    author: str
    stance: str  # "pro" | "con" | "neutral"
    claim: str
    reasoning: str
    quote: str
    comment_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RejectedAlternative:
    name: str
    proposer: str
    rejection_reasons: List[str]
    key_objection_quote: str
    objection_author: str
    comment_id: str
    comment_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceQuote:
    id: str
    quote: str
    author: str
    comment_id: str
    comment_url: str
    verified: bool = False
    confidence: float = 0.0
    context: str = ""
    char_offset: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionRecord:
    id: str
    discussion_id: str
    title: str
    status: str  # Accepted, Rejected, Superseded, Proposed
    date: str
    context: str
    problem_statement: str
    decision_outcome: str
    accepted_option: str
    considered_options: List[str]
    rejected_alternatives: List[RejectedAlternative]
    consequences_positive: List[str]
    consequences_negative: List[str]
    affected_components: List[str]
    evidence_quotes: List[EvidenceQuote]
    madr_content: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "discussion_id": self.discussion_id,
            "title": self.title,
            "status": self.status,
            "date": self.date,
            "context": self.context,
            "problem_statement": self.problem_statement,
            "decision_outcome": self.decision_outcome,
            "accepted_option": self.accepted_option,
            "considered_options": self.considered_options,
            "rejected_alternatives": [
                ra.to_dict() for ra in self.rejected_alternatives
            ],
            "consequences_positive": self.consequences_positive,
            "consequences_negative": self.consequences_negative,
            "affected_components": self.affected_components,
            "evidence_quotes": [eq.to_dict() for eq in self.evidence_quotes],
            "madr_content": self.madr_content,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionRecord:
        rejected_alts = [
            RejectedAlternative(**ra)
            for ra in data.get("rejected_alternatives", [])
        ]
        evidence_quotes = [
            EvidenceQuote(**eq) for eq in data.get("evidence_quotes", [])
        ]
        return cls(
            id=data["id"],
            discussion_id=data.get("discussion_id", ""),
            title=data.get("title", ""),
            status=data.get("status", "Accepted"),
            date=data.get("date", ""),
            context=data.get("context", ""),
            problem_statement=data.get("problem_statement", ""),
            decision_outcome=data.get("decision_outcome", ""),
            accepted_option=data.get("accepted_option", ""),
            considered_options=data.get("considered_options", []),
            rejected_alternatives=rejected_alts,
            consequences_positive=data.get("consequences_positive", []),
            consequences_negative=data.get("consequences_negative", []),
            affected_components=data.get("affected_components", []),
            evidence_quotes=evidence_quotes,
            madr_content=data.get("madr_content", ""),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
        )


@dataclass
class PipelineStageResult:
    stage_num: int
    stage_name: str
    model_name: str
    execution_time_ms: float
    output: Dict[str, Any]
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineExecutionResult:
    discussion_id: str
    stages: List[PipelineStageResult]
    final_decision: DecisionRecord
    total_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discussion_id": self.discussion_id,
            "stages": [s.to_dict() for s in self.stages],
            "final_decision": self.final_decision.to_dict(),
            "total_time_ms": self.total_time_ms,
        }


@dataclass
class PullRequestDiff:
    pr_id: str
    title: str
    description: str
    changed_files: List[str]
    patch_diff: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RadarAlert:
    id: str
    pr_id: str
    severity: str  # "high" | "medium" | "low" | "info"
    matched_decision_id: str
    matched_decision_title: str
    conflict_type: str  # "resurrected_rejected_alternative" | "architectural_deviation" | "precedent_reference"
    message: str
    historical_context: str
    matched_files: List[str]
    rejected_alternative: Optional[str] = None
    rejection_reason: Optional[str] = None
    evidence_link: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
