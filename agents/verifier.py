"""Group 2: turn evidence into sourced claims and preserve contradictions."""

# Input: external tool results and internal retrieved chunks.
# Output: atomic-ish Claim dictionaries plus unresolved conflict records.

from __future__ import annotations

import re
from typing import Any

from models.schemas import Claim


DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
IMMEDIATE_PATTERN = re.compile(r"\b(immediately|effective immediately|at once)\b", re.I)
SCOPE_PATTERN = re.compile(r"\b(controls apply|covers|covered|restricted|ban|only to|only those)\b", re.I)


def _authority(source_type: str) -> str:
    """Map source categories to the shared broad authority labels."""
    kind = source_type.casefold()
    if kind in {"government", "internal"}:
        return "primary"
    if kind == "news":
        return "secondary"
    return "unknown"


def _source_root(item: dict[str, Any]) -> str:
    """Treat a syndicated article and its original as one corroborating source."""
    return str(item.get("duplicate_of") or item.get("source_id") or item.get("id", "unknown"))


def _claim_confidence(authority: str, independent_count: int) -> float:
    """Use authority and independent confirmation as separate, transparent signals."""
    authority_base = {"primary": 0.86, "secondary": 0.58, "unknown": 0.40}[authority]
    corroboration_bonus = min(0.12, max(0, independent_count - 1) * 0.06)
    return round(min(0.99, authority_base + corroboration_bonus), 2)


def _external_claims(state: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
    source_items = [
        ("news_articles", "news"),
        ("government_evidence", "government"),
        ("market_evidence", "market"),
    ]
    for collection_name, default_type in source_items:
        for item in state.get(collection_name, []):
            # Suspicious retrieved instructions remain in audit state but are
            # excluded from factual claim extraction.
            if item.get("injection_flagged"):
                continue
            source_id = str(item.get("source_id") or item.get("id") or "")
            if not source_id:
                continue
            source_type = str(item.get("source_type", default_type))
            authority = _authority(source_type)
            source_date = str(item.get("date", ""))
            snippet = str(item.get("snippet") or item.get("text") or item.get("title") or "").strip()
            if not snippet:
                continue
            source_root = _source_root(item)
            dates = DATE_PATTERN.findall(snippet)

            # Extract one effective-date claim when a source states a date or says "immediately".
            if dates and re.search(r"\b(effective|takes effect|start|begin|date)\b", snippet, re.I):
                date_value = dates[0]
                claims.append({
                    "claim_id": f"{source_id}-effective-date",
                    "text": f"Controls take effect on {date_value}.",
                    "claim_type": "effective_date",
                    "source_ids": [source_id],
                    "source_authority": authority,
                    "source_date": source_date,
                    "confidence": _claim_confidence(authority, 1),
                    "status": "supported" if authority == "primary" else "unverified",
                    "independent_source_count": 1,
                    "claim_value": date_value,
                    "_source_root": source_root,
                })
            elif IMMEDIATE_PATTERN.search(snippet) and re.search(r"\b(effective|controls|restriction|take effect)\b", snippet, re.I):
                claims.append({
                    "claim_id": f"{source_id}-effective-date",
                    "text": "Controls take effect immediately.",
                    "claim_type": "effective_date",
                    "source_ids": [source_id],
                    "source_authority": authority,
                    "source_date": source_date,
                    "confidence": _claim_confidence(authority, 1),
                    "status": "unverified",
                    "independent_source_count": 1,
                    "claim_value": "immediately",
                    "_source_root": source_root,
                })

            # Keep the source's own scope statement intact; never blend differing scopes.
            has_explicit_scope = bool(
                SCOPE_PATTERN.search(snippet)
                and not re.search(
                    r"\b(?:does not|doesn't|cannot|unable to)\s+"
                    r"(?:establish|confirm|determine)\b",
                    snippet,
                    re.I,
                )
            )
            if has_explicit_scope:
                claims.append({
                    "claim_id": f"{source_id}-scope",
                    "text": snippet,
                    "claim_type": "scope",
                    "source_ids": [source_id],
                    "source_authority": authority,
                    "source_date": source_date,
                    "confidence": _claim_confidence(authority, 1),
                    "status": "supported" if authority == "primary" else "unverified",
                    "independent_source_count": 1,
                    "claim_value": re.sub(r"\W+", " ", snippet.casefold()).strip(),
                    "_source_root": source_root,
                })

            # Record other material supplier or viral statements as claims too.
            if (
                re.search(r"\b(unaffected|unverified|viral|ban|delivery|deliveries)\b", snippet, re.I)
                and not (authority == "primary" and has_explicit_scope)
            ):
                claim_type = (
                    "supplier_statement"
                    if source_type == "company" or re.search(r"\bunaffected\b", snippet, re.I)
                    else "unverified_report"
                )
                claims.append({
                    "claim_id": f"{source_id}-statement",
                    "text": f"{item.get('title', '')}: {snippet}".strip(": "),
                    "claim_type": claim_type,
                    "source_ids": [source_id],
                    "source_authority": authority,
                    "source_date": source_date,
                    "confidence": _claim_confidence(authority, 1),
                    "status": "unverified",
                    "independent_source_count": 1,
                    "claim_value": re.sub(r"\W+", " ", snippet.casefold()).strip(),
                    "_source_root": source_root,
                })
    return claims


def _internal_claims(state: dict[str, Any]) -> list[Claim]:
    """Represent retrieved internal passages as sourced facts, not free-floating prose."""
    claims: list[Claim] = []
    for index, document in enumerate(state.get("internal_documents", []), start=1):
        if document.get("metadata", {}).get("injection_flagged"):
            continue
        source_id = str(document.get("source_id", ""))
        text = str(document.get("text", "")).strip()
        if not source_id or not text:
            continue
        claims.append({
            "claim_id": f"internal-{index}",
            "text": text,
            "claim_type": "internal_context",
            "source_ids": [source_id],
            "source_authority": "primary",
            "source_date": str(document.get("metadata", {}).get("doc_date", "")),
            "confidence": round(max(0.4, min(0.95, float(document.get("score", 0.7)))), 2),
            "status": "supported",
            "independent_source_count": 1,
            "_source_root": source_id,
        })
    return claims


def _deduplicate_claims(claims: list[Claim]) -> list[Claim]:
    """Merge exact duplicate assertions while counting duplicate copies once."""
    merged: dict[tuple[str, str], Claim] = {}
    roots: dict[tuple[str, str], set[str]] = {}
    for claim in claims:
        claim_value = claim.get("claim_value") or re.sub(
            r"\W+",
            " ",
            claim["text"].casefold(),
        ).strip()
        key = (claim["claim_type"], claim_value)
        if key not in merged:
            merged[key] = {field: value for field, value in claim.items() if not field.startswith("_")}
            roots[key] = set()
        root = str(claim.get("_source_root", claim["source_ids"][0]))
        roots[key].add(root)
        existing = merged[key]
        existing["source_ids"] = sorted(set(existing["source_ids"] + claim["source_ids"]))
        existing["independent_source_count"] = len(roots[key])
        authority_rank = {"unknown": 0, "secondary": 1, "primary": 2}
        if authority_rank[claim["source_authority"]] > authority_rank[existing["source_authority"]]:
            # A primary source supporting the same assertion improves the claim's
            # authority; repeated secondary copies must not outrank it.
            existing["source_authority"] = claim["source_authority"]
            existing["source_date"] = claim["source_date"]
            existing["status"] = claim["status"]
        existing["confidence"] = _claim_confidence(
            existing["source_authority"],
            len(roots[key]),
        )
    return list(merged.values())


def verify_claims(state: dict[str, Any]) -> dict[str, Any]:
    """Extract evidence-backed claims and flag disagreements without resolving them."""
    raw_claims = _external_claims(state) + _internal_claims(state)
    claims = _deduplicate_claims(raw_claims)

    # Claims of the same type with different values are potential contradictions.
    groups: dict[str, list[Claim]] = {}
    for claim in claims:
        if claim["claim_type"] in {"effective_date", "scope"}:
            groups.setdefault(claim["claim_type"], []).append(claim)
    conflicts: list[dict[str, Any]] = []
    for claim_type, related in groups.items():
        distinct_values = {str(claim.get("claim_value") or claim["text"]) for claim in related}
        if len(distinct_values) < 2:
            continue
        conflict_id = f"conflict-{claim_type}"
        claim_ids = [claim["claim_id"] for claim in related]
        source_ids = sorted({source_id for claim in related for source_id in claim["source_ids"]})
        for claim in related:
            claim["status"] = "contradicted"
        conflicts.append({
            "conflict_id": conflict_id,
            "claim_type": claim_type,
            "description": f"Sources disagree about {claim_type.replace('_', ' ')}; both positions are preserved.",
            "claim_ids": claim_ids,
            "source_ids": source_ids,
            "status": "unresolved",
        })

    # A supplier's reassurance may not address whether its product is covered
    # by an official control. Keep both statements visible when internal mapping
    # connects that supplier to the controlled product category.
    impacted_suppliers = {
        str(item.get("name", "")).casefold()
        for item in state.get("impacted_suppliers", [])
        if item.get("name")
    }
    supplier_claims = [
        claim for claim in claims
        if claim["claim_type"] == "supplier_statement"
        and any(name in claim["text"].casefold() for name in impacted_suppliers)
    ]
    primary_scope_claims = [
        claim for claim in claims
        if claim["claim_type"] == "scope"
        and claim["source_authority"] == "primary"
    ]
    if supplier_claims and primary_scope_claims:
        related = supplier_claims + primary_scope_claims
        for claim in supplier_claims:
            claim["status"] = "contradicted"
        conflicts.append({
            "conflict_id": "conflict-supplier-impact",
            "claim_type": "supplier_impact",
            "description": (
                "The supplier says deliveries are unaffected, while an official notice and "
                "internal product mapping indicate the supplied component may be in scope."
            ),
            "claim_ids": [claim["claim_id"] for claim in related],
            "source_ids": sorted({
                source_id for claim in related for source_id in claim["source_ids"]
            }),
            "status": "unresolved",
        })

    source_ids = sorted({
        source_id
        for claim in claims
        for source_id in claim["source_ids"]
    })
    independent_sources = {
        str(item.get("duplicate_of") or item.get("source_id") or item.get("id"))
        for key in ("news_articles", "government_evidence", "market_evidence")
        for item in state.get(key, [])
    }
    independent_sources.update(
        str(item.get("source_id"))
        for item in state.get("internal_documents", [])
        if item.get("source_id")
    )
    primary_count = sum(claim["source_authority"] == "primary" for claim in claims)
    if claims:
        confidence = round(
            sum(claim["confidence"] for claim in claims) / len(claims),
            2,
        )
    else:
        confidence = 0.0
    if conflicts:
        confidence = min(confidence, 0.65)
    return {
        "claims": claims,
        "conflicting_claims": conflicts,
        "source_ids": source_ids,
        "source_count": len(source_ids),
        "independent_source_count": len(independent_sources),
        "confidence_score": confidence,
    }
