"""choose safe graph branches and keep research loops bounded."""

# Input: the latest shared state after a guardrail or evidence-gate node.
# Output: the next named graph node.

from __future__ import annotations

from typing import Any

from guardrails.budgets import budget_remaining


def route_after_input(state: dict[str, Any]) -> str:
    """Continue only when the initial question passed the guardrail."""
    return "analyze_query" if state.get("input_allowed") else "reject_input"


def route_after_evidence(state: dict[str, Any]) -> str:
    """Research again only when requested and the iteration budget remains."""
    result = state.get("evidence_gate_result")
    if result == "needs_research" and budget_remaining(state):
        return "investigate_more"
    # Both a sufficient-evidence pass and a safe budget-exhaustion stop proceed
    # to risk scoring; the report keeps any uncertainty visible.
    return "assess_risk"

