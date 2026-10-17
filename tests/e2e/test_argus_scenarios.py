"""ARGUS scenario tests."""

from __future__ import annotations

import pytest

from graph.graph import run_investigation
from rag.ingest import build_index


@pytest.fixture(scope="module", autouse=True)
def indexed_internal_corpus():
    build_index()


def test_semiconductor_export_restriction_path_has_evidence_risk_and_actions():
    result = run_investigation(
        "There are reports of new semiconductor export restrictions. "
        "Investigate what changed, check whether our suppliers/products may be exposed, "
        "estimate risk and recommend next actions.",
        max_investigation_iterations=4,
    )
    assert result["government_evidence"]
    assert result["internal_documents"]
    assert result["claims"]
    assert result["conflicting_claims"]
    assert {item["name"] for item in result["impacted_suppliers"]} == {"Cirrus Silicon"}
    assert {item["name"] for item in result["impacted_products"]} == {"Helios Edge"}
    assert any(conflict["claim_type"] == "supplier_impact" for conflict in result["conflicting_claims"])
    assert result["risk_score"] > 0
    assert 0 <= result["confidence_score"] <= 1
    assert result["recommended_actions"]
    assert "LIMITATIONS AND UNKNOWN INFORMATION" in result["final_report"]
    assert "EVIDENCE REVIEWED" in result["final_report"]
    assert "UNVERIFIED OR DISPUTED CLAIMS" in result["final_report"]
    assert "mock data" in result["final_report"].casefold()


def test_tool_failure_ends_safely_with_transparent_limitation():
    result = run_investigation(
        "Investigate semiconductor export restrictions and Northstar supplier exposure",
        max_investigation_iterations=2,
        simulate_tool_failures=True,
    )
    assert result["final_report"]
    assert result["investigation_iterations"] <= 2
    assert result["errors"]
    assert any("error" in line.casefold() or "failed" in line.casefold()
               for line in result["evidence_limitations"])


def test_unverified_viral_claim_is_not_reported_as_a_verified_fact():
    result = run_investigation(
        "Investigate reports of a viral consumer electronics export ban and Northstar exposure",
        max_investigation_iterations=2,
    )
    assert result["news_articles"]
    assert "not verified" in result["final_report"].casefold()


def test_unmatched_supplier_disruption_does_not_report_unrelated_export_controls():
    result = run_investigation(
        "I heard there may be a new supplier disruption, but I don't know which supplier. "
        "What can you verify, and what remains unknown?",
        max_investigation_iterations=4,
    )

    assert result["news_articles"] == []
    assert result["government_evidence"] == []
    assert "no matching external event evidence was found" in result["final_report"].casefold()
    assert "gov-001" not in result["final_report"]
    assert "news-001" not in result["final_report"]
    assert "unresolved evidence conflict" not in result["final_report"].casefold()
