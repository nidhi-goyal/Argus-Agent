"""run a small repeatable benchmark over all benchmark datasets."""

# Run with: python -m evaluation.regression
# This benchmark evaluates retrieval and answer/agent behavior as separate metrics.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.news_investigator import expected_tool_for_query
from agents.risk_analyst import assess_risk
from agents.verifier import verify_claims
from evaluation.metrics import (
    claim_grounding,
    citation_coverage,
    contradiction_recall,
    retrieval_precision,
    risk_classification_accuracy,
    summarize_metrics,
    tool_selection_accuracy,
)
from guardrails.evidence import evidence_gate
from graph.state import new_state
from mcp.government_client import search_regulation
from mcp.news_client import search_news
from rag.retrieval import search_internal


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "evaluation" / "datasets"


def _load(name: str) -> Any:
    """Read one labelled JSON dataset and fail clearly if it is missing or invalid."""
    path = DATASETS / name
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_regression() -> dict[str, float]:
    """Run retrieval, tool-choice, seeded-conflict, grounding, and risk checks."""
    metrics: dict[str, float] = {}

    # see whether the expected source document appears in the top five.
    retrieval_cases = _load("g1_retrieval_qa.json")
    retrieval_hits = 0
    for case in retrieval_cases:
        results = search_internal(case["prompt"], top_k=5)
        retrieval_hits += any(
            item["source_id"].startswith(case["expected_source"] + "#")
            for item in results
        )
    metrics["Retrieval source hit rate"] = retrieval_precision(retrieval_hits, len(retrieval_cases))

    # score deterministic first-tool choices from the labelled questions.
    orchestration = _load("g2_agents.json")
    tool_cases = [
        {
            "expected_tool": case["expected_tool"],
            "selected_tool": expected_tool_for_query(case["query"]),
        }
        for case in orchestration["tool_cases"]
    ]
    metrics["Tool selection accuracy"] = tool_selection_accuracy(tool_cases)

    # Run the mock event through the verifier to measure whether its planted
    # effective-date contradiction is still detectable.
    mock_news = search_news("semiconductor export accelerator")
    mock_gov = search_regulation("semiconductor export accelerator")
    verified = verify_claims({
        "news_articles": mock_news["items"],
        "government_evidence": mock_gov["items"],
        "internal_documents": search_internal(
            "semiconductor export accelerator supplier exposure",
            top_k=5,
        ),
    })
    metrics["Seeded contradiction recall"] = contradiction_recall(
        orchestration["seeded_conflicts"],
        verified["conflicting_claims"],
    )
    metrics["Claim grounding"] = claim_grounding(verified["claims"])
    metrics["Citation coverage"] = citation_coverage(verified["claims"])

    # score the labelled risk examples using the production risk function.
    quality = _load("g3_trust_quality.json")
    risk_cases = []
    for case in quality["risk_cases"]:
        assessment = assess_risk({
            "risk_dimensions": case["dimensions"],
            "claims": [],
            "independent_source_count": case.get("independent_source_count", 0),
        })
        risk_cases.append({"actual": assessment["risk_level"], "expected": case["expected_level"]})
    metrics["Risk classification accuracy"] = risk_classification_accuracy(risk_cases)

    gate_cases = []
    for case in quality["evidence_gate_cases"]:
        state = new_state(case["query"])
        state.update(case["state"])
        gate_cases.append({
            "actual": evidence_gate(state),
            "expected": case["expected_gate"],
        })
    metrics["Evidence sufficiency accuracy"] = (
        sum(case["actual"] == case["expected"] for case in gate_cases) / len(gate_cases)
        if gate_cases else 0.0
    )
    return metrics


def main() -> int:
    """Print the benchmark result and return a success status."""
    metrics = run_regression()
    print("ARGUS REGRESSION METRICS")
    print(summarize_metrics(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
