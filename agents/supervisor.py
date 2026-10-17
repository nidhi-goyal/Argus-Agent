"""understand the executive question and prepare an investigation plan."""

# Input: IntelligenceState with the user's question.
# Output: objective, recognized entities, needed evidence, and the initial missing facts.

from __future__ import annotations

import json
import re
from typing import Any

from models.cascade import call_model, parse_json_object


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

    model_prompt = json.dumps({
        "question": query,
        "known_entities": list(KNOWN_ENTITIES),
        "allowed_evidence_categories": [
            "external event evidence",
            "internal supplier/product exposure",
            "authoritative regulatory scope and effective date",
            "independent secondary reporting",
        ],
    }, ensure_ascii=False)
    model_text, model_call = call_model(
        "small",
        "query_planning",
        "Extract only what is explicitly present in the question. Return one JSON object with "
        "objective (a concise search query), entities, companies, countries, and evidence_needed. "
        "Do not invent facts or add evidence categories outside the supplied list.",
        model_prompt,
    )
    model_calls = list(state.get("model_calls", []))
    if model_call:
        model_calls.append(model_call)
    parsed = parse_json_object(model_text)
    if parsed:
        proposed_objective = parsed.get("objective")
        if isinstance(proposed_objective, str) and proposed_objective.strip():
            objective = proposed_objective.strip()[:1000]

        # Only keep entities the model can point to in the user's actual question.
        mentioned_entities = parsed.get("entities", [])
        if isinstance(mentioned_entities, list):
            for name in mentioned_entities:
                if isinstance(name, str) and name.strip() and name.casefold() in query.casefold():
                    if name not in entities:
                        entities.append(name)
        model_companies = parsed.get("companies", [])
        if isinstance(model_companies, list):
            companies.extend(
                name for name in model_companies
                if isinstance(name, str) and name in entities and name not in companies
            )
        model_countries = parsed.get("countries", [])
        if isinstance(model_countries, list):
            countries.extend(
                name for name in model_countries
                if isinstance(name, str) and name in entities and name not in countries
            )
        allowed_categories = {
            "external event evidence",
            "internal supplier/product exposure",
            "authoritative regulatory scope and effective date",
            "independent secondary reporting",
        }
        proposed_needs = parsed.get("evidence_needed", [])
        if isinstance(proposed_needs, list):
            evidence_needed.extend(
                item for item in proposed_needs
                if isinstance(item, str) and item in allowed_categories and item not in evidence_needed
            )

    updates = {
        "investigation_objective": objective,
        "entities": entities,
        "companies": companies,
        "countries": countries,
        "evidence_needed": evidence_needed,
        "missing_information": evidence_needed.copy(),
    }
    if model_calls != list(state.get("model_calls", [])):
        updates["model_calls"] = model_calls
    return updates
