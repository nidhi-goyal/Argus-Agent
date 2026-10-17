"""LangGraph execution, routing, investigation, and claims."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.news_investigator import choose_next_tool, investigate_more
from agents.verifier import verify_claims
from graph.graph import build_graph, run_investigation
from graph.routing import route_after_evidence
from graph.state import new_state
from mcp.government_client import search_regulation
from mcp.news_client import search_news
from rag.ingest import build_index


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", autouse=True)
def indexed_sample_data():
    build_index()


def test_graph_compiles_and_runs_to_a_final_report():
    graph = build_graph()
    state = new_state("Investigate semiconductor export restrictions and Northstar exposure")
    state["max_investigation_iterations"] = 2
    result = graph.invoke(state)
    assert result["final_report"].startswith("ARGUS GLOBAL RISK INTELLIGENCE REPORT")
    assert result["investigation_iterations"] <= 2
    assert result["risk_score"] > 0


def test_routing_pass_and_budget_rules():
    assert route_after_evidence({"evidence_gate_result": "pass", "investigation_iterations": 0}) == "assess_risk"
    assert route_after_evidence({
        "evidence_gate_result": "needs_research",
        "investigation_iterations": 0,
        "max_investigation_iterations": 2,
    }) == "investigate_more"
    assert route_after_evidence({
        "evidence_gate_result": "needs_research",
        "investigation_iterations": 2,
        "max_investigation_iterations": 2,
    }) == "assess_risk"
    assert route_after_evidence({"evidence_gate_result": "stop_with_uncertainty"}) == "assess_risk"


def test_graph_loop_terminates_at_iteration_limit(monkeypatch):
    import graph.graph as graph_module

    monkeypatch.setattr(graph_module, "evidence_gate", lambda state: "needs_research")
    state = new_state("Investigate supplier risk news", max_investigation_iterations=2)
    result = build_graph().invoke(state)
    assert result["investigation_iterations"] == 2
    assert result["final_report"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Investigate export-control regulation scope", "search_regulation"),
        ("There are news reports of a supplier disruption", "search_news"),
        ("Which Northstar supplier provides the Helios Edge component?", "search_internal"),
    ],
)
def test_supervisor_tool_choice_matches_evidence_type(query, expected):
    assert choose_next_tool({"user_query": query}) == expected


def test_investigator_records_one_tool_observation_and_iteration():
    state = new_state("Investigate semiconductor export restrictions")
    update = investigate_more(state)
    assert update["investigation_iterations"] == 1
    assert update["tool_calls"]
    assert update["observations"]
    assert update["observations"][0]["tool"] == "search_regulation"
    assert update["observations"][0]["status"] == "ok"


def test_investigator_uses_alternate_source_after_failed_tool():
    state = new_state(
        "Investigate semiconductor export restrictions",
        simulate_tool_failures={"search_regulation": True},
    )
    update = investigate_more(state)
    assert update["investigation_iterations"] == 1
    assert any(call["status"] == "error" for call in update["tool_calls"])
    assert any(call.get("fallback_for") == "search_regulation" for call in update["tool_calls"])
    assert update["observations"][0]["status"] == "ok"
    assert update["errors"]


def test_verifier_flags_effective_date_conflict_and_preserves_provenance():
    news = search_news("semiconductor export accelerator")
    government = search_regulation("semiconductor export accelerator")
    result = verify_claims({
        "news_articles": news["items"],
        "government_evidence": government["items"],
        "internal_documents": [],
    })
    date_claims = [claim for claim in result["claims"] if claim["claim_type"] == "effective_date"]
    assert date_claims
    assert all(claim["source_ids"] for claim in date_claims)
    assert any(conflict["claim_type"] == "effective_date" for conflict in result["conflicting_claims"])


def test_duplicate_articles_are_not_counted_as_independent_confirmation():
    news = search_news("semiconductor export accelerator")
    result = verify_claims({"news_articles": news["items"], "government_evidence": []})
    repeated_claims = [
        claim for claim in result["claims"]
        if claim["claim_type"] == "effective_date" and "2026-09-01" in claim["text"]
    ]
    assert repeated_claims
    assert all(claim["independent_source_count"] < len(claim["source_ids"]) for claim in repeated_claims)
    copies = [item for item in news["items"] if item.get("duplicate_of") == "news-001"]
    assert len(copies) >= 1


def test_seeded_group2_dataset_has_cases_for_all_required_tool_types():
    dataset = json.loads((ROOT / "evaluation" / "datasets" / "g2_agents.json").read_text(encoding="utf-8"))
    assert {case["expected_tool"] for case in dataset["tool_cases"]} == {
        "search_news", "search_regulation", "search_internal"
    }
    assert any(case["claim_type"] == "effective_date" for case in dataset["seeded_conflicts"])


def test_invalid_question_takes_safe_rejection_path():
    result = run_investigation("Tell me a joke")
    assert result["input_allowed"] is False
    assert "did not start" in result["final_report"]
