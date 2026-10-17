"""shared typed data shapes used across ARGUS components."""

# Input: fields returned by tools, RAG, and workflow agents.
# Output: reusable TypedDict contracts that document each exchanged dictionary.

# These TypedDicts document the dictionaries exchanged between agents.
# They make expected fields clear without requiring runtime model parsing.

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


ToolStatus = Literal["ok", "empty", "error"]
ClaimStatus = Literal["supported", "unverified", "contradicted"]
EvidenceAuthority = Literal["primary", "secondary", "unknown"]


class Evidence(TypedDict):
    """One traceable observation returned by an internal or external source."""

    source_id: str
    source: str
    date: str
    text: str
    source_type: str
    authority: EvidenceAuthority
    mock: bool
    url: NotRequired[str]
    duplicate_of: NotRequired[str]


class ToolResult(TypedDict):
    """Shared result contract: empty searches and failed tools are distinct."""

    status: ToolStatus
    mock: bool
    items: list[dict[str, Any]]
    error: str | None


class RetrievedChunk(TypedDict):
    """An internal document excerpt returned by the RAG search."""

    text: str
    source_id: str
    metadata: dict[str, Any]
    score: float


class Claim(TypedDict):
    """A single factual assertion with source provenance and confidence."""

    claim_id: str
    text: str
    claim_type: str
    source_ids: list[str]
    source_authority: EvidenceAuthority
    source_date: str
    confidence: float
    status: ClaimStatus
    independent_source_count: NotRequired[int]
    claim_value: NotRequired[str]


class RiskAssessment(TypedDict):
    """Risk, confidence, and evidence quality are reported separately."""

    impact: float
    probability: float
    urgency: float
    risk_score: float
    risk_level: Literal["low", "medium", "high"]
    confidence_score: float
    evidence_quality_score: float
    formula: str


class RecommendedAction(TypedDict):
    """A proposed human-owned action; ARGUS never executes it."""

    priority: int
    owner: Literal["procurement", "legal", "operations", "leadership"]
    action: str
    rationale: str
    evidence_ids: list[str]
    requires_human_approval: bool
