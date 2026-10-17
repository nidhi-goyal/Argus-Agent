"""compile the LangGraph workflow that runs an ARGUS investigation."""

# Input: an executive question wrapped in IntelligenceState.
# Output: the final state after bounded investigation, verification, risk,
# recommendations, evaluation, and report generation.

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.evaluator import evaluate_answer, generate_report
from agents.news_investigator import investigate_more
from agents.recommender import recommend_actions
from agents.risk_analyst import assess_risk
from agents.supervisor import analyze_query
from agents.verifier import verify_claims
from config.settings import SETTINGS
from graph.routing import route_after_evidence, route_after_input
from graph.state import IntelligenceState
from guardrails.evidence import evidence_gate
from guardrails.injection import check_input, sanitize_retrieved_text
from agents.internal_analyst import analyze_internal_exposure


def check_input_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run the input guardrail before any external or internal search begins."""
    decision = check_input(str(state.get("user_query", "")))
    return {
        "input_allowed": decision["allowed"],
        "input_rejection_reason": decision["reason"],
    }


def reject_input_node(state: dict[str, Any]) -> dict[str, Any]:
    """Finish safely with a short explanation when a query is rejected."""
    reason = str(state.get("input_rejection_reason", "Question was not accepted."))
    return {
        "evaluation_result": {
            "passed": False,
            "checks": {"input_allowed": False},
            "reason": reason,
        },
        "final_report": f"ARGUS did not start the investigation.\n\nReason: {reason}",
    }


def discover_external_evidence(state: dict[str, Any]) -> dict[str, Any]:
    """Let the ReAct investigator choose a tool and gather one observation."""
    return investigate_more(state)


def retrieve_internal_context(state: dict[str, Any]) -> dict[str, Any]:
    """Map discovered events to internal suppliers/products and flag injected text."""
    updates = analyze_internal_exposure(state)
    flagged_ids = list(state.get("injection_flags", []))
    safe_documents: list[dict[str, Any]] = []
    for original in updates.get("internal_documents", []):
        document = dict(original)
        sanitized = sanitize_retrieved_text(str(document.get("text", "")))
        metadata = dict(document.get("metadata", {}))
        if sanitized["flagged"]:
            metadata["injection_flagged"] = True
            flagged_ids.append(str(document.get("source_id", "unknown internal source")))
        document["metadata"] = metadata
        safe_documents.append(document)

    # Apply the same untrusted-content check to text returned by mock external tools.
    evidence_updates: dict[str, Any] = {}
    for key in ("news_articles", "government_evidence", "market_evidence"):
        sanitized_items = []
        for original in state.get(key, []):
            item = dict(original)
            text = " ".join(str(item.get(field, "")) for field in ("title", "snippet", "text"))
            sanitized = sanitize_retrieved_text(text)
            if sanitized["flagged"]:
                item["injection_flagged"] = True
                flagged_ids.append(str(item.get("source_id", "unknown external source")))
            sanitized_items.append(item)
        evidence_updates[key] = sanitized_items

    missing = list(state.get("missing_information", []))
    analyst_missing = updates.get("missing_information", [])
    if analyst_missing:
        missing.extend(analyst_missing)
    else:
        missing = [
            item for item in missing
            if "internal supplier/product exposure" not in item.casefold()
            and "internal document" not in item.casefold()
        ]
    # This node returns only the state fields it owns. Merge its evidence with the
    # existing tool observations instead of dropping anything gathered earlier.
    existing_documents = list(state.get("internal_documents", []))
    by_source = {str(item.get("source_id")): item for item in existing_documents}
    for document in safe_documents:
        by_source[str(document.get("source_id"))] = document
    return {
        **evidence_updates,
        "internal_documents": list(by_source.values()),
        "impacted_suppliers": updates.get("impacted_suppliers", []),
        "impacted_products": updates.get("impacted_products", []),
        "missing_information": list(dict.fromkeys(missing)),
        "injection_flags": list(dict.fromkeys(flagged_ids)),
    }


def verify_claims_node(state: dict[str, Any]) -> dict[str, Any]:
    """Extract source-linked claims and preserve any disagreement between sources."""
    return verify_claims(state)


def evidence_gate_node(state: dict[str, Any]) -> dict[str, Any]:
    """Store the evidence gate decision so LangGraph can choose a conditional edge."""
    return {"evidence_gate_result": evidence_gate(state)}


def build_graph():
    """Create and compile the finite-state workflow described in the assignment."""
    workflow = StateGraph(IntelligenceState)
    workflow.add_node("check_input", check_input_node)
    workflow.add_node("reject_input", reject_input_node)
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("discover_external_evidence", discover_external_evidence)
    workflow.add_node("retrieve_internal_context", retrieve_internal_context)
    workflow.add_node("verify_claims", verify_claims_node)
    workflow.add_node("evidence_gate", evidence_gate_node)
    workflow.add_node("investigate_more", investigate_more)
    workflow.add_node("assess_risk", assess_risk)
    workflow.add_node("recommend_actions", recommend_actions)
    workflow.add_node("evaluate_answer", evaluate_answer)
    workflow.add_node("generate_report", generate_report)

    # The input check either ends safely or starts the actual evidence workflow.
    workflow.add_edge(START, "check_input")
    workflow.add_conditional_edges(
        "check_input",
        route_after_input,
        {"analyze_query": "analyze_query", "reject_input": "reject_input"},
    )
    workflow.add_edge("reject_input", END)

    # Normal path: question -> external evidence -> internal context -> verification.
    workflow.add_edge("analyze_query", "discover_external_evidence")
    workflow.add_edge("discover_external_evidence", "retrieve_internal_context")
    workflow.add_edge("retrieve_internal_context", "verify_claims")
    workflow.add_edge("verify_claims", "evidence_gate")

    # Research loops back to verification and is capped by the shared iteration limit.
    workflow.add_conditional_edges(
        "evidence_gate",
        route_after_evidence,
        {"investigate_more": "investigate_more", "assess_risk": "assess_risk"},
    )
    workflow.add_edge("investigate_more", "verify_claims")

    # Every non-rejected run reaches the same risk, action, quality, and report steps.
    workflow.add_edge("assess_risk", "recommend_actions")
    workflow.add_edge("recommend_actions", "evaluate_answer")
    workflow.add_edge("evaluate_answer", "generate_report")
    workflow.add_edge("generate_report", END)
    return workflow.compile()


def run_investigation(user_query: str, **overrides: Any) -> IntelligenceState:
    """Run the compiled graph for one question and return its completed state."""
    from graph.state import new_state

    defaults = {
        "max_investigation_iterations": SETTINGS.max_investigation_iterations,
        "top_k": SETTINGS.top_k,
    }
    defaults.update(overrides)
    state = new_state(user_query, **defaults)
    return build_graph().invoke(state)
