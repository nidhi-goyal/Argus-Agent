"""calculate explicit quality measures over labelled ARGUS examples."""

# Retrieval precision remains separate from grounding and answer quality so a
# retrieval failure can be distinguished from a reasoning/reporting failure.

from __future__ import annotations

from typing import Any


def retrieval_precision(relevant_retrieved: int, retrieved_count: int) -> float:
    """Return relevant retrieved chunks divided by all retrieved chunks."""
    if retrieved_count <= 0:
        return 0.0
    return relevant_retrieved / retrieved_count


def tool_selection_accuracy(cases: list[dict[str, Any]]) -> float:
    """Measure how often the selected tool matches the labelled expected tool."""
    if not cases:
        return 0.0
    correct = sum(case.get("selected_tool") == case.get("expected_tool") for case in cases)
    return correct / len(cases)


def contradiction_recall(seeded_conflicts: list[dict[str, Any]], detected_conflicts: list[dict[str, Any]]) -> float:
    """Measure what fraction of labelled conflicts the verifier detected."""
    if not seeded_conflicts:
        return 1.0
    detected_types = {item.get("claim_type") for item in detected_conflicts}
    found = sum(item.get("claim_type") in detected_types for item in seeded_conflicts)
    return found / len(seeded_conflicts)


def claim_grounding(claims: list[dict[str, Any]]) -> float:
    """Measure claims with at least one source ID and a supported status."""
    if not claims:
        return 0.0
    grounded = sum(bool(claim.get("source_ids")) and claim.get("status") == "supported" for claim in claims)
    return grounded / len(claims)


def citation_coverage(claims: list[dict[str, Any]]) -> float:
    """Measure decision claims with source IDs, independent of whether supported."""
    if not claims:
        return 0.0
    cited = sum(bool(claim.get("source_ids")) for claim in claims)
    return cited / len(claims)


def evidence_sufficiency_accuracy(cases: list[dict[str, Any]]) -> float:
    """Compare the gate's actual decision with each scenario's expected decision."""
    if not cases:
        return 0.0
    correct = sum(case.get("actual") == case.get("expected") for case in cases)
    return correct / len(cases)


def risk_classification_accuracy(cases: list[dict[str, Any]]) -> float:
    """Compare calculated low/medium/high risk levels with expert labels."""
    if not cases:
        return 0.0
    correct = sum(case.get("actual") == case.get("expected") for case in cases)
    return correct / len(cases)


def summarize_metrics(metrics: dict[str, float]) -> str:
    """Format metric values as a short human-readable evaluation summary."""
    return "\n".join(f"{name}: {value:.1%}" for name, value in metrics.items())

