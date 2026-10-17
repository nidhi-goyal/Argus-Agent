"""mock government/regulatory search client."""

# ARGUS workflow: external evidence discovery, called when regulatory evidence is needed.
# Input: search words, an optional jurisdiction, and an optional failure-test switch.
# Output: ToolResult-style dictionary containing mock notices or an explicit empty/error status.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.search_utils import search_terms


MOCK_FILE = Path(__file__).resolve().parents[1] / "data" / "mock" / "regulations.json"


def search_regulation(
    query: str,
    jurisdiction: str | None = None,
    *,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    """Search fictional official notices and return the shared ToolResult shape.

    The source records are examples, not real government information. The
    jurisdiction argument can narrow the results to a particular region.
    """
    # Simulated failures allow investigators to test graceful degradation.
    if simulate_failure:
        return {
            "status": "error",
            "mock": True,
            "items": [],
            "error": "Simulated government search timeout.",
        }
    # Require an actual search phrase before accessing the source data.
    if not query or not query.strip():
        raise ValueError("query must contain non-whitespace text")
    # Read the local mock-notice file and keep data problems distinct from no matches.
    try:
        entries = json.loads(MOCK_FILE.read_text(encoding="utf-8"))
    except OSError as exc:
        return {"status": "error", "mock": True, "items": [], "error": f"Unable to read mock regulation data: {exc}"}
    except json.JSONDecodeError as exc:
        return {"status": "error", "mock": True, "items": [], "error": f"Invalid mock regulation data: {exc}"}

    # Ignore generic prompt words so broad questions do not match unrelated notices.
    terms = search_terms(query)
    if not terms:
        return {"status": "empty", "mock": True, "items": [], "error": None}
    matches: list[dict[str, Any]] = []
    for entry in entries:
        # Include notice title, description, region, tags, and publisher in the search.
        searchable = " ".join(
            str(entry.get(key, ""))
            for key in ("title", "snippet", "jurisdiction", "tags", "source")
        ).casefold()
        if terms and not any(term in searchable for term in terms):
            continue
        # If requested, require the notice jurisdiction to match the given text.
        if jurisdiction and jurisdiction.casefold() not in str(entry.get("jurisdiction", "")).casefold():
            continue
        # Keep the external tool response small and consistent with the shared contract.
        item = {key: entry[key] for key in ("title", "source", "url", "date", "snippet", "source_type")}
        item["mock"] = True
        item["source_id"] = str(entry["id"])
        matches.append(item)
    # An empty result is a successful search with no matching notices.
    return {
        "status": "ok" if matches else "empty",
        "mock": True,
        "items": matches,
        "error": None,
    }
