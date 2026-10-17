"""check grounding and produce the final decision-oriented report."""

# Input: the completed investigation state.
# Output: evaluation checklist and a report that separates evidence, inference,
# uncertainty, and proposed actions.

from __future__ import annotations

from typing import Any


def evaluate_answer(state: dict[str, Any]) -> dict[str, Any]:
    """Check whether material claims have sources and conflicts are disclosed."""
    claims = state.get("claims", [])
    unsupported = [
        claim.get("claim_id", claim.get("text", "unknown claim"))
        for claim in claims
        if not claim.get("source_ids") or claim.get("status") == "unsupported"
    ]
    unverified = [
        claim.get("claim_id", "unknown claim")
        for claim in claims
        if claim.get("status") == "unverified"
    ]
    cited_claims = [claim for claim in claims if claim.get("source_ids")]
    citation_coverage = len(cited_claims) / len(claims) if claims else 0.0
    supported_claims = [
        claim for claim in claims
        if claim.get("source_ids") and claim.get("status") == "supported"
    ]
    conflicts = state.get("conflicting_claims", [])
    has_evidence = bool(claims or state.get("news_articles") or state.get("government_evidence"))
    checks = {
        "relevance": bool(str(state.get("user_query", "")).strip()),
        "grounding": not unsupported,
        "unsupported_claims": unsupported,
        "unverified_claims": unverified,
        "citation_coverage": round(citation_coverage, 3),
        "contradictions_disclosed": bool(not conflicts or all(
            conflict.get("status") == "unresolved" for conflict in conflicts
        )),
        "completeness": bool(state.get("risk_level") and state.get("recommended_actions") is not None),
        "evidence_present": has_evidence,
    }
    passed = (
        checks["relevance"]
        and checks["grounding"]
        and checks["contradictions_disclosed"]
        and checks["completeness"]
    )
    return {
        "evaluation_result": {
            "passed": passed,
            "checks": checks,
            "supported_claim_count": len(supported_claims),
            "claim_count": len(claims),
        }
    }


def _format_claims(state: dict[str, Any]) -> list[str]:
    """Format supported, non-conflicted claims with their traceable source IDs."""
    lines: list[str] = []
    for claim in state.get("claims", []):
        if claim.get("status") != "supported" or not claim.get("source_ids"):
            continue
        if claim.get("claim_type") == "scope":
            # The report's facts should stay concise; the full source remains cited.
            text = str(claim.get("text", "")).strip()
            if len(text) > 240:
                text = text[:237].rstrip() + "..."
        else:
            text = str(claim.get("text", "")).strip()
        if len(text) > 320:
            text = text[:317].rstrip() + "..."
        if text:
            citations = ", ".join(str(source_id) for source_id in claim["source_ids"])
            lines.append(f"- {text} [Sources: {citations}]")
    return lines[:6]


def _evidence_summary(state: dict[str, Any]) -> list[str]:
    """List the sources ARGUS actually reviewed so readers can audit the report."""
    collections = (
        ("Government notices", "government_evidence"),
        ("News/company reports", "news_articles"),
        ("Market sources", "market_evidence"),
        ("Internal documents", "internal_documents"),
    )
    lines: list[str] = []
    for label, key in collections:
        items = state.get(key, [])
        if not items:
            continue
        identifiers = sorted({
            str(item.get("source_id") or item.get("id"))
            for item in items
            if item.get("source_id") or item.get("id")
        })
        lines.append(
            f"- {label}: {len(items)} item(s); source IDs: "
            f"{', '.join(identifiers) if identifiers else 'not supplied'}."
        )
    return lines


def _unverified_claim_lines(state: dict[str, Any]) -> list[str]:
    """Show sourced but unverified claims with clear caveats instead of treating them as facts."""
    lines: list[str] = []
    for claim in state.get("claims", []):
        if claim.get("status") not in {"unverified", "contradicted"}:
            continue
        text = str(claim.get("text", "")).strip()
        if len(text) > 220:
            text = text[:217].rstrip() + "..."
        source_ids = ", ".join(claim.get("source_ids", [])) or "no source ID"
        label = "DISPUTED" if claim.get("status") == "contradicted" else "NOT VERIFIED"
        lines.append(f"- {label}: {text} [Source: {source_ids}]")
    return lines[:5]


def generate_report(state: dict[str, Any]) -> dict[str, Any]:
    """Create an honest executive summary without filling gaps with guesses."""
    query = str(state.get("user_query", ""))
    claims = state.get("claims", [])
    facts = _format_claims(state)
    suppliers = [str(item.get("name", "")) for item in state.get("impacted_suppliers", [])]
    products = [str(item.get("name", "")) for item in state.get("impacted_products", [])]
    conflicts = state.get("conflicting_claims", [])
    actions = state.get("recommended_actions", [])
    risk_score = float(state.get("risk_score", 0.0))
    confidence = float(state.get("confidence_score", 0.0))
    quality = float(state.get("evidence_quality_score", 0.0))

    # Keep facts, interpretation, and uncertainty in separate report sections.
    report_lines = [
        "ARGUS GLOBAL RISK INTELLIGENCE REPORT",
        "",
        f"Question: {query}",
        "",
        "FACTS FROM AVAILABLE EVIDENCE",
    ]
    has_external_event_evidence = any(
        state.get(key)
        for key in ("news_articles", "government_evidence", "market_evidence")
    )
    if not has_external_event_evidence:
        report_lines.append(
            "- No matching external event evidence was found in the available sources."
        )
    report_lines.extend(facts or ["- Unknown: available sources do not establish a verified event fact."])
    report_lines.extend([
        "",
        "EVIDENCE REVIEWED",
    ])
    report_lines.extend(_evidence_summary(state) or ["- No source items were returned."])
    report_lines.extend([
        "",
        "UNVERIFIED OR DISPUTED CLAIMS",
    ])
    report_lines.extend(
        _unverified_claim_lines(state)
        or ["- No separately unverified or contradicted claim was retained."]
    )
    report_lines.extend([
        "",
        "BUSINESS EXPOSURE",
        f"- Potentially affected suppliers: {', '.join(suppliers) if suppliers else 'Unknown / not established.'}",
        f"- Potentially affected products: {', '.join(products) if products else 'Unknown / not established.'}",
        "",
        "RISK AND CONFIDENCE",
        f"- Risk: {state.get('risk_level', 'unknown').upper()} ({risk_score:.2f}/10).",
        f"- Dimensions (1-10): impact {float(state.get('impact_score', 0.0)):.1f}, "
        f"probability {float(state.get('probability_score', 0.0)):.1f}, "
        f"urgency {float(state.get('urgency_score', 0.0)):.1f}.",
        f"- Confidence in the evidence-based assessment: {confidence:.0%}.",
        f"- Evidence quality: {quality:.0%}. These measures are separate from risk.",
        f"- Scoring method: {state.get('risk_formula', 'Not available.')}.",
        "",
        "INFERENCE",
    ])
    if products and suppliers:
        report_lines.append(
            f"- Internal mappings connect {', '.join(suppliers)} to {', '.join(products)}; "
            "this indicates potential exposure, not proof that deliveries will stop."
        )
    else:
        report_lines.append("- No company-specific exposure conclusion is established by the retrieved mapping evidence.")

    report_lines.extend(["", "UNRESOLVED CONFLICTS"])
    if conflicts:
        for conflict in conflicts:
            report_lines.append(
                f"- {conflict.get('description', 'Sources disagree.')} "
                f"Source IDs: {', '.join(conflict.get('source_ids', [])) or 'not available'}."
            )
    else:
        report_lines.append("- No material conflict was identified in the evidence reviewed.")

    report_lines.extend(["", "RECOMMENDED ACTIONS (PROPOSED; NOT EXECUTED)"])
    if actions:
        for action in actions:
            approval = "Human approval required" if action.get("requires_human_approval") else "Human approval not required"
            report_lines.append(
                f"{action.get('priority', '?')}. [{str(action.get('owner', 'owner')).title()}] "
                f"{action.get('action', '')} - {approval}. "
                f"Evidence: {', '.join(action.get('evidence_ids', [])) or 'none'}."
            )
    else:
        report_lines.append("Unknown: no evidence-linked action could be generated.")

    report_lines.extend(["", "LIMITATIONS AND UNKNOWN INFORMATION"])
    limitations = list(state.get("evidence_limitations", []))
    limitations.extend(state.get("missing_information", []))
    if any(item.get("mock") for key in ("news_articles", "government_evidence", "market_evidence") for item in state.get(key, [])):
        limitations.append("External intelligence is fictional mock data; this report is not live-world intelligence.")
    if not claims:
        limitations.append("No source-backed claims were extracted; event details remain unknown.")
    if state.get("injection_flags"):
        limitations.append("Prompt-injection-like text was found in evidence and treated as untrusted data.")
    if limitations:
        for limitation in dict.fromkeys(limitations):
            report_lines.append(f"- {limitation}")
    else:
        report_lines.append("- No additional limitations were recorded.")

    model_calls = list(state.get("model_calls", []))
    report_lines.extend(["", "MODEL CASCADE TELEMETRY"])
    if not model_calls:
        report_lines.append(
            "- No model API requests were recorded; deterministic local processing was used."
        )
    else:
        successful_calls = [call for call in model_calls if call.get("status") == "ok"]
        total_cost = sum(float(call.get("estimated_cost_usd", 0.0)) for call in successful_calls)
        total_latency = sum(float(call.get("latency_ms", 0.0)) for call in model_calls)
        total_tokens = sum(
            int(call.get("input_tokens", 0)) + int(call.get("output_tokens", 0))
            for call in successful_calls
        )
        for call in model_calls:
            detail = (
                f"- {call.get('tier', 'unknown')} / {call.get('model', 'unknown')} "
                f"({call.get('operation', 'model call')}): {call.get('status', 'unknown')}, "
                f"{float(call.get('latency_ms', 0.0)):.0f} ms, "
                f"estimated $ {float(call.get('estimated_cost_usd', 0.0)):.6f}"
            )
            if call.get("evidence_candidates") is not None:
                detail += (
                    f"; evidence filtered {call['evidence_candidates']} -> "
                    f"{call.get('evidence_sent', 0)} excerpts"
                )
            if call.get("error_type"):
                detail += f"; {call['error_type']} fallback used"
            report_lines.append(detail)
        report_lines.append(
            f"- Total: {len(successful_calls)} successful requests, {total_tokens} tokens, "
            f"{total_latency:.0f} ms, estimated $ {total_cost:.6f}."
        )

    return {"final_report": "\n".join(report_lines)}
