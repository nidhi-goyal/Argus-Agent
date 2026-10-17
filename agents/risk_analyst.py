"""calculate a transparent impact, probability, and urgency risk score."""

# Input: verified claims, internal exposure, and optional labelled score dimensions.
# Output: risk score/level, confidence, and evidence quality as separate values.

from __future__ import annotations

from typing import Any

from config.settings import SETTINGS


def _clamp_dimension(value: Any, name: str) -> float:
    """Convert a dimension to a number on the agreed 1-to-10 scale."""
    number = float(value)
    if not 1.0 <= number <= 10.0:
        raise ValueError(f"{name} must be between 1 and 10")
    return number


def _derived_dimensions(state: dict[str, Any]) -> tuple[float, float, float]:
    """Estimate missing score inputs from the evidence and exposure already gathered."""
    suppliers = state.get("impacted_suppliers", [])
    products = state.get("impacted_products", [])
    has_official_source = bool(state.get("government_evidence"))
    conflicts = state.get("conflicting_claims", [])

    # A specifically affected product is more consequential than a generic headline.
    impact = 2.0 if not suppliers else min(9.0, 5.5 + len(products) * 0.8)
    # Official evidence increases the likelihood that the external event is real.
    probability = 6.5 if has_official_source and suppliers else 3.0 if not has_official_source else 5.0
    # Unresolved contradictions increase the need for prompt review, not factual certainty.
    urgency = 7.0 if conflicts else 6.0 if suppliers else 3.0
    return impact, probability, urgency


def assess_risk(state: dict[str, Any]) -> dict[str, Any]:
    """Calculate a repeatable weighted score and keep evidence confidence separate."""
    supplied = state.get("risk_dimensions", {})
    default_impact, default_probability, default_urgency = _derived_dimensions(state)
    impact = _clamp_dimension(supplied.get("impact", default_impact), "impact")
    probability = _clamp_dimension(
        supplied.get("probability", default_probability),
        "probability",
    )
    urgency = _clamp_dimension(supplied.get("urgency", default_urgency), "urgency")

    # Weighted average stays on a 1–10 scale; configured weights must total 1.
    score = round(
        impact * SETTINGS.risk_weight_impact
        + probability * SETTINGS.risk_weight_probability
        + urgency * SETTINGS.risk_weight_urgency,
        2,
    )
    risk_level = "high" if score >= 7.0 else "medium" if score >= 4.0 else "low"

    claims = state.get("claims", [])
    source_ids = {
        source_id
        for claim in claims
        for source_id in claim.get("source_ids", [])
    }
    if not source_ids:
        source_ids.update(
            str(item.get("source_id"))
            for key in ("news_articles", "government_evidence", "internal_documents")
            for item in state.get(key, [])
            if item.get("source_id")
        )
    primary_claims = sum(
        claim.get("source_authority") == "primary"
        for claim in claims
    )
    independent_count = int(state.get("independent_source_count", len(source_ids)))
    # Evidence quality rewards traceable, independent primary evidence and falls
    # when material contradictions remain unresolved.
    evidence_quality = min(
        1.0,
        0.15 * bool(source_ids)
        + 0.25 * min(1.0, independent_count / 3)
        + 0.35 * bool(primary_claims or state.get("government_evidence"))
        + 0.25 * bool(state.get("internal_documents")),
    )
    if state.get("conflicting_claims"):
        evidence_quality *= 0.75
    confidence = float(state.get("confidence_score", 0.0))
    if not claims and confidence == 0.0:
        confidence = min(0.45, evidence_quality * 0.6)

    return {
        "impact_score": impact,
        "probability_score": probability,
        "urgency_score": urgency,
        "risk_score": score,
        "risk_level": risk_level,
        "confidence_score": round(max(0.0, min(1.0, confidence)), 2),
        "evidence_quality_score": round(evidence_quality, 2),
        "risk_formula": (
            f"risk = impact*{SETTINGS.risk_weight_impact:.2f} + "
            f"probability*{SETTINGS.risk_weight_probability:.2f} + "
            f"urgency*{SETTINGS.risk_weight_urgency:.2f}"
        ),
    }
