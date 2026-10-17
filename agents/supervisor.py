"""Group 2: understand the executive question and prepare an investigation plan."""

# Input: IntelligenceState with the user's question.
# Output: objective, recognized entities, needed evidence, and the initial missing facts.

from __future__ import annotations

import re
from typing import Any


KNOWN_ENTITIES = (
    "Northstar Instruments", "Cirrus Silicon", "Kestrel Components",
    "Lumen Foundry", "Oriole Packaging", "Helios Edge", "Beacon Gateway",
    "Aurora Array", "Meridian Sensor", "Atlas Controller", "China",
)
COMPANY_NAMES = {
    "Northstar Instruments", "Cirrus Silicon", "Kestrel Components",
    "Lumen Foundry", "Oriole Packaging",
}
COUNTRY_NAMES = {"China", "United States", "North America", "Asia-Pacific"}
REGULATORY_WORDS = re.compile(r"\b(regulation|regulatory|export control|export restriction|ban|sanction|law|rule)\b", re.I)


def analyze_query(state: dict[str, Any]) -> dict[str, Any]:
    """Extract the objective and entities using a lightweight, deterministic parser."""
    query = str(state.get("user_query", "")).strip()
    if not query:
        raise ValueError("state must include a non-empty user_query")

    # Match known fictional organizations/products first so multiword names stay whole.
    entities = [name for name in KNOWN_ENTITIES if name.casefold() in query.casefold()]
    # Also capture title-cased phrases supplied by the user that are not in the demo list.
    for match in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", query):
        if match not in entities:
            entities.append(match)
    companies = [name for name in entities if name in COMPANY_NAMES]
    countries = [name for name in entities if name in COUNTRY_NAMES]

    # An executive question normally needs both outside event evidence and internal exposure.
    evidence_needed = ["external event evidence", "internal supplier/product exposure"]
    if REGULATORY_WORDS.search(query):
        evidence_needed.insert(0, "authoritative regulatory scope and effective date")
        evidence_needed.append("independent secondary reporting")
    objective = query

    return {
        "investigation_objective": objective,
        "entities": entities,
        "companies": companies,
        "countries": countries,
        "evidence_needed": evidence_needed,
        "missing_information": evidence_needed.copy(),
    }
