"""decide if evidence supports a conclusion or more research is needed."""

# The graph uses this gate to control its loop; the gate never trusts a model to
# decide by itself that research is complete.

from __future__ import annotations

from typing import Any, Literal

from config.settings import SETTINGS
from guardrails.budgets import budget_remaining


GateResult = Literal["pass", "needs_research", "stop_with_uncertainty"]


def _independent_source_ids(state: dict[str, Any]) -> set[str]:
    """Return unique source IDs, treating copied articles as their original source.

    ``state`` is the shared investigation data. Its news, government, and market
    lists contain external sources; ``internal_documents`` contains company
    documents. A set is used because sets automatically keep only unique IDs.
    """
    independent: set[str] = set()
    # External search results may include syndicated copies. ``duplicate_of``
    # points to the original article, so count that ID instead of the copy's ID.
    # Fall back to this item's source_id (or older id field) when it is original.
    for collection_name in ("news_articles", "government_evidence", "market_evidence"):
        for item in state.get(collection_name, []):
            source_id = str(item.get("duplicate_of") or item.get("source_id") or item.get("id", ""))
            if source_id:
                independent.add(source_id)
    # Internal documents have their own source IDs and are counted individually.
    for item in state.get("internal_documents", []):
        source_id = str(item.get("source_id", ""))
        if source_id:
            independent.add(source_id)
    # The set lets the gate compare the number of distinct sources with its minimum.
    return independent


def evidence_gate(state: dict[str, Any]) -> GateResult:
    """Decide if the investigation should research again or proceed to risk scoring.

    The graph calls this after gathering and checking evidence. It returns one
    of three labels: ``pass`` means the evidence checks are satisfied;
    ``needs_research`` means something important is missing or weak; and
    ``stop_with_uncertainty`` means the research-cycle limit has been reached.
    This is a sufficiency check, not a guarantee that a conclusion is true.
    """
    # Check the budget first: even weak or conflicting evidence cannot trigger
    # another research loop after the configured maximum number of cycles.
    if not budget_remaining(state):
        return "stop_with_uncertainty"

    # Read evidence and verification results written by earlier graph steps.
    conflicts = state.get("conflicting_claims", [])
    missing = state.get("missing_information", [])
    sources = _independent_source_ids(state)
    # Only a government source counts as primary external evidence here.
    has_primary_external = any(
        str(item.get("source_type", "")).casefold() == "government"
        for item in state.get("government_evidence", [])
    )
    # The gate also requires internal documents to assess company-specific exposure.
    has_internal_context = bool(state.get("internal_documents"))
    # Confidence is expected to be a number from 0.0 to 1.0.
    confidence = float(state.get("confidence_score", 0.0))

    # Conflicts or outstanding information needs always request more research
    # while budget remains; they should not be hidden by a high confidence score.
    if conflicts or missing:
        return "needs_research"

    # "pass" requires every configured sufficiency condition, not just one:
    # enough confidence, enough distinct sources, an official source, and
    # internal company context.
    if (
        confidence >= SETTINGS.confidence_threshold
        and len(sources) >= SETTINGS.minimum_independent_sources
        and has_primary_external
        and has_internal_context
    ):
        return "pass"

    # Evidence is incomplete or below a configured threshold, but the budget
    # check above says another research cycle is still permitted.
    return "needs_research"
