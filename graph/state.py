"""shared state that carries information through the ARGUS graph."""

# Every graph node reads this dictionary and returns only the keys it updates.
# Initial values are created by new_state so loops always start with fresh lists.

from __future__ import annotations

from typing import Any, TypedDict


class IntelligenceState(TypedDict, total=False):
    """Names and types of information passed between investigation steps."""

    user_query: str
    investigation_objective: str
    entities: list[str]
    companies: list[str]
    countries: list[str]
    evidence_needed: list[str]
    input_allowed: bool
    input_rejection_reason: str
    news_articles: list[dict[str, Any]]
    government_evidence: list[dict[str, Any]]
    market_evidence: list[dict[str, Any]]
    internal_documents: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    conflicting_claims: list[dict[str, Any]]
    impacted_suppliers: list[dict[str, Any]]
    impacted_products: list[dict[str, Any]]
    missing_information: list[str]
    investigation_iterations: int
    evidence_gate_result: str
    risk_score: float
    risk_level: str
    impact_score: float
    probability_score: float
    urgency_score: float
    confidence_score: float
    evidence_quality_score: float
    risk_formula: str
    recommended_actions: list[dict[str, Any]]
    evaluation_result: dict[str, Any]
    final_report: str
    errors: list[str]
    model_calls: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    tool_selection_accuracy: list[dict[str, Any]]
    injection_flags: list[str]
    source_count: int
    independent_source_count: int
    source_ids: list[str]
    risk_dimensions: dict[str, float]
    simulate_tool_failures: bool | dict[str, bool]
    top_k: int
    max_investigation_iterations: int
    timeout_seconds: float
    retry_limit: int
    risk_justification: str
    evidence_limitations: list[str]


def new_state(user_query: str, **overrides: Any) -> IntelligenceState:
    """Create a ready-to-run state dictionary with safe empty defaults."""
    if not user_query or not user_query.strip():
        raise ValueError("user_query must contain non-whitespace text")
    # Lists and dictionaries must be newly created per run so investigations
    # cannot accidentally share or overwrite each other's evidence.
    state: IntelligenceState = {
        "user_query": user_query.strip(),
        "investigation_objective": user_query.strip(),
        "entities": [],
        "companies": [],
        "countries": [],
        "evidence_needed": [],
        "news_articles": [],
        "government_evidence": [],
        "market_evidence": [],
        "internal_documents": [],
        "claims": [],
        "conflicting_claims": [],
        "impacted_suppliers": [],
        "impacted_products": [],
        "missing_information": [],
        "investigation_iterations": 0,
        "evidence_gate_result": "needs_research",
        "risk_score": 0.0,
        "risk_level": "low",
        "impact_score": 1.0,
        "probability_score": 1.0,
        "urgency_score": 1.0,
        "confidence_score": 0.0,
        "evidence_quality_score": 0.0,
        "recommended_actions": [],
        "evaluation_result": {},
        "final_report": "",
        "errors": [],
        "model_calls": [],
        "tool_calls": [],
        "observations": [],
        "tool_selection_accuracy": [],
        "injection_flags": [],
        "source_count": 0,
        "independent_source_count": 0,
        "source_ids": [],
        "risk_dimensions": {},
        "simulate_tool_failures": False,
        "evidence_limitations": [],
    }
    # Allow callers and tests to seed explicit situations, such as tool failures.
    state.update(overrides)
    return state
