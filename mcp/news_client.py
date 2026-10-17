"""mock news search client with explicit empty/error result states."""

# ARGUS workflow: external evidence discovery, called by the news investigator.
# Input: search words and optional date/region filters; failure simulation is for tests.
# Output: ToolResult-style dictionary with status, mock flag, matching articles, and error.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.search_utils import search_terms


MOCK_FILE = Path(__file__).resolve().parents[1] / "data" / "mock" / "news.json"


def _tool_error(message: str) -> dict[str, Any]:
    """Build a consistent error response instead of pretending a failure is no results."""
    return {"status": "error", "mock": True, "items": [], "error": message}


def search_news(
    query: str,
    date_range: tuple[str, str] | None = None,
    region: str | None = None,
    *,
    simulate_failure: bool = False,
) -> dict[str, Any]:
    """Search the clearly labeled local mock-news corpus.

    Results are mock examples, not live reporting. A caller can filter matches
    by date and region, or simulate a timeout to test failure handling.
    """
    # Let tests check safe handling of unavailable tools without changing files or network.
    if simulate_failure:
        return _tool_error("Simulated news tool timeout.")
    # Reject incomplete requests before reading the mock data.
    if not query or not query.strip():
        raise ValueError("query must contain non-whitespace text")
    if date_range and len(date_range) != 2:
        raise ValueError("date_range must contain an inclusive start and end date")
    # Read the local JSON corpus; report file or JSON problems as tool errors.
    try:
        entries = json.loads(MOCK_FILE.read_text(encoding="utf-8"))
    except OSError as exc:
        return _tool_error(f"Unable to read mock news data: {exc}")
    except json.JSONDecodeError as exc:
        return _tool_error(f"Invalid mock news data: {exc}")

    # Ignore generic prompt words so broad questions do not match unrelated stories.
    terms = search_terms(query)
    if not terms:
        return {"status": "empty", "mock": True, "items": [], "error": None}
    matches: list[dict[str, Any]] = []
    for entry in entries:
        # Search across the fields that describe what the article is about.
        searchable = " ".join(
            str(entry.get(key, ""))
            for key in ("title", "snippet", "source", "region", "tags")
        ).casefold()
        if terms and not any(term in searchable for term in terms):
            continue
        # Apply optional filters after the text match to narrow results.
        if region and region.casefold() not in str(entry.get("region", "")).casefold():
            continue
        entry_date = str(entry.get("date", ""))
        if date_range and not (date_range[0] <= entry_date <= date_range[1]):
            continue
        # Return the agreed public fields, with mock/source IDs for traceability.
        item = {key: entry[key] for key in ("title", "source", "url", "date", "snippet", "source_type")}
        item["mock"] = True
        item["source_id"] = str(entry["id"])
        if entry.get("duplicate_of"):
            item["duplicate_of"] = str(entry["duplicate_of"])
        matches.append(item)
    # "empty" means the search worked but found nothing; it is different from "error".
    return {
        "status": "ok" if matches else "empty",
        "mock": True,
        "items": matches,
        "error": None,
    }
