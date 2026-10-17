"""Group 3: decide if evidence supports a conclusion or more research is needed."""

# The graph uses this gate to control its loop; the gate never trusts a model to
# decide by itself that research is complete.

from __future__ import annotations

from typing import Any, Literal

from config.settings import SETTINGS
from guardrails.budgets import budget_remaining


GateResult = Literal["pass", "needs_research", "stop_with_uncertainty"]


def _independent_source_ids(state: dict[str, Any]) -> set[str]:
    """Count source records once, grouping syndicated copies under their original."""
    independent: set[str] = set()
    for collection_name in ("news_articles", "government_evidence", "market_evidence"):
        for item in state.get(collection_name, []):
            source_id = str(item.get("duplicate_of") or item.get("source_id") or item.get("id", ""))
            if source_id:
                independent.add(source_id)
    for item in state.get("internal_documents", []):
        source_id = str(item.get("source_id", ""))
        if source_id:
            independent.add(source_id)
    return independent


def evidence_gate(state: dict[str, Any]) -> GateResult:
    """Return pass, research, or uncertainty based on evidence and remaining budget."""
    # If no more calls are permitted, finish safely with the known limitations.
    if not budget_remaining(state):
        return "stop_with_uncertainty"

    conflicts = state.get("conflicting_claims", [])
    missing = state.get("missing_information", [])
    sources = _independent_source_ids(state)
    has_primary_external = any(
        str(item.get("source_type", "")).casefold() == "government"
        for item in state.get("government_evidence", [])
    )
    has_internal_context = bool(state.get("internal_documents"))
    confidence = float(state.get("confidence_score", 0.0))

    # Material conflicts and missing required facts must be researched, not hidden.
    if conflicts or missing:
        return "needs_research"
    if (
        confidence >= SETTINGS.confidence_threshold
        and len(sources) >= SETTINGS.minimum_independent_sources
        and has_primary_external
        and has_internal_context
    ):
        return "pass"
    return "needs_research"

