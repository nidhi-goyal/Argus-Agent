"""suggest prioritized, evidence-linked actions for human decision makers."""

# Input: risk scores, impacted suppliers/products, evidence, and unresolved gaps.
# Output: RecommendedAction dictionaries; this module never executes an action.

from __future__ import annotations

from typing import Any


def recommend_actions(state: dict[str, Any]) -> dict[str, Any]:
    """Create specific next steps and mark consequential actions for approval."""
    source_ids = sorted({
        source_id
        for collection in (
            state.get("claims", []),
            state.get("internal_documents", []),
            state.get("news_articles", []),
            state.get("government_evidence", []),
        )
        for item in collection
        for source_id in (
            item.get("source_ids", [])
            if isinstance(item.get("source_ids"), list)
            else [item.get("source_id", "")]
        )
        if source_id
    })
    suppliers = [item.get("name", "supplier") for item in state.get("impacted_suppliers", [])]
    products = [item.get("name", "product") for item in state.get("impacted_products", [])]
    conflicts = state.get("conflicting_claims", [])
    risk_level = str(state.get("risk_level", "low"))
    actions: list[dict[str, Any]] = []
    internal_ids = sorted({
        str(item.get("source_id"))
        for item in state.get("internal_documents", [])
        if item.get("source_id")
    })
    government_ids = sorted({
        str(item.get("source_id"))
        for item in state.get("government_evidence", [])
        if item.get("source_id")
    })
    supplier_statement_ids = sorted({
        str(source_id)
        for claim in state.get("claims", [])
        if claim.get("claim_type") == "supplier_statement"
        for source_id in claim.get("source_ids", [])
    })
    conflict_ids = sorted({
        str(source_id)
        for conflict in conflicts
        for source_id in conflict.get("source_ids", [])
    })

    if suppliers:
        # Supplier and procurement steps can affect business commitments, so they
        # are always presented for human approval rather than performed by ARGUS.
        actions.append({
            "priority": 1,
            "owner": "procurement",
            "action": f"Verify current inventory, committed deliveries, and lead times with {', '.join(suppliers)}.",
            "rationale": (
                f"Internal evidence maps the event to {', '.join(products) or 'a product'}; "
                "confirm the current operational exposure before changing plans."
            ),
            "evidence_ids": sorted(set(internal_ids + supplier_statement_ids)) or source_ids[:5],
            "requires_human_approval": True,
        })
        actions.append({
            "priority": 2,
            "owner": "legal",
            "action": "Review the official notice and confirm whether the affected components and destinations are in scope.",
            "rationale": "Regulatory classification and supplier communications require qualified human review.",
            "evidence_ids": sorted(set(government_ids + conflict_ids)) or source_ids[:5],
            "requires_human_approval": True,
        })
        actions.append({
            "priority": 3,
            "owner": "operations",
            "action": f"Assess qualified alternatives and continuity options for {', '.join(products) or 'affected products'}.",
            "rationale": "Prepare mitigations without making an unapproved procurement change.",
            "evidence_ids": internal_ids or source_ids[:5],
            "requires_human_approval": True,
        })
    else:
        actions.append({
            "priority": 1,
            "owner": "operations",
            "action": "Confirm whether any internal supplier, component, or product is exposed.",
            "rationale": "Available evidence did not establish a product or supplier connection.",
            "evidence_ids": conflict_ids or source_ids[:5],
            "requires_human_approval": False,
        })

    if conflicts:
        actions.append({
            "priority": 1 if not suppliers else 2,
            "owner": "legal",
            "action": "Review the unresolved evidence conflict and obtain clarification from an authoritative source.",
            "rationale": "Conflicting or missing evidence prevents a fully certain conclusion.",
            "evidence_ids": conflict_ids or source_ids[:5],
            "requires_human_approval": True,
        })
    elif state.get("missing_information"):
        actions.append({
            "priority": 2 if suppliers else 1,
            "owner": "leadership",
            "action": "Identify the missing information and seek a relevant authoritative source before drawing a conclusion.",
            "rationale": "The available sources did not establish all facts needed to assess the event.",
            "evidence_ids": source_ids[:5],
            "requires_human_approval": True,
        })
    if risk_level == "high":
        actions.append({
            "priority": 1,
            "owner": "leadership",
            "action": "Review the risk assessment and decide whether to activate the business continuity escalation.",
            "rationale": "The calculated risk is high; approval and operational authority remain with leadership.",
            "evidence_ids": source_ids,
            "requires_human_approval": True,
        })

    # Stable priority ordering gives the same inputs the same action order.
    actions.sort(key=lambda item: (item["priority"], item["owner"], item["action"]))
    return {"recommended_actions": actions}
