"""one bounded Think -> Act -> Observe investigation step."""

# Input: the current question, gathered evidence, tool history, and research budget.
# Output: new tool observations, updated evidence lists, and an incremented iteration count.

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import json
import re
from typing import Any, Callable

from models.cascade import call_model, parse_json_object

from mcp.government_client import search_regulation
from mcp.news_client import search_news
from rag.retrieval import search_internal
from guardrails.budgets import budget_remaining, retry_limit, tool_timeout_seconds


REGULATION_TERMS = re.compile(
    r"\b(regulation|regulations|regulatory|export controls?|export restrictions?|"
    r"ban|bans|sanction|sanctions|law|laws|rule|rules)\b",
    re.I,
)
EVENT_TERMS = re.compile(
    r"\b(reports?|news|events?|announcements?|restrictions?|incidents?|"
    r"outbreaks?|conflicts?|markets?|geopolit)\b",
    re.I,
)


def expected_tool_for_query(query: str) -> str:
    """Return which kind of source is most appropriate for an untouched query."""
    # A request specifically about reports or a viral claim should first locate
    # those reports; explicit official/regulatory questions start with government.
    if re.search(r"\b(news|reports?|articles?|viral|rumou?r)\b", query, re.I) and not re.search(
        r"\b(official|government|regulation|regulatory|notice|effective date)\b",
        query,
        re.I,
    ):
        return "search_news"
    if REGULATION_TERMS.search(query):
        return "search_regulation"
    if EVENT_TERMS.search(query):
        return "search_news"
    return "search_internal"


def choose_next_tool(state: dict[str, Any]) -> str:
    """Select the next tool based on the question and which tools already worked."""
    query = str(state.get("investigation_objective") or state.get("user_query") or "")
    expected = expected_tool_for_query(query)
    successful = {
        str(call.get("tool"))
        for call in state.get("tool_calls", [])
        if call.get("status") in {"ok", "empty"}
    }
    # For regulatory questions, consult the official source first, then seek news.
    if expected == "search_regulation" and "search_regulation" not in successful:
        return "search_regulation"
    if expected == "search_news" and "search_news" not in successful:
        return "search_news"
    if expected == "search_internal" and "search_internal" not in successful:
        return "search_internal"
    # Once the primary source has been checked, use a different source for comparison.
    if "search_news" not in successful:
        return "search_news"
    if "search_regulation" not in successful:
        return "search_regulation"

    # After general reporting and official evidence, look for a statement from
    # a specifically exposed supplier found by the internal analyst.
    for supplier in (
        item.get("name", "")
        for item in state.get("impacted_suppliers", [])
        if item.get("name")
    ):
        supplier_was_checked = any(
            call.get("target_supplier") == supplier and call.get("status") in {"ok", "empty"}
            for call in state.get("tool_calls", [])
        )
        if not supplier_was_checked:
            return "search_news"
    if expected == "search_internal":
        return "search_internal"
    return "search_internal"


def _choose_tool_with_model(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Use the small tier for tool routing, then validate against available tools."""
    fallback = choose_next_tool(state)
    successful = {
        str(call.get("tool"))
        for call in state.get("tool_calls", [])
        if call.get("status") in {"ok", "empty"}
    }
    available = [
        tool for tool in ("search_news", "search_regulation", "search_internal")
        if tool not in successful
    ]
    if fallback not in available and not available:
        available = [fallback]
    elif fallback not in available:
        available.append(fallback)

    prompt = json.dumps({
        "question": str(state.get("investigation_objective") or state.get("user_query") or ""),
        "missing_information": list(state.get("missing_information", [])),
        "successful_tools": sorted(successful),
        "available_tools": available,
        "supplier_names": [
            item.get("name") for item in state.get("impacted_suppliers", []) if item.get("name")
        ],
    }, ensure_ascii=False)
    output, telemetry = call_model(
        "small",
        "tool_selection",
        "Choose the next useful source category from available_tools. Return only a JSON object "
        'like {"tool":"search_news"}. Do not invent tools or claim evidence was found.',
        prompt,
    )
    parsed = parse_json_object(output)
    selected = parsed.get("tool") if parsed else None
    accepted = selected in available
    if not accepted:
        selected = fallback
    if telemetry:
        telemetry["selected_tool"] = selected
        telemetry["model_selection_accepted"] = accepted
    return str(selected), telemetry


def _run_with_timeout(
    function: Callable[..., dict[str, Any]],
    timeout: float,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run one tool call with a maximum wait, returning a clear timeout error."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(function, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeout:
        future.cancel()
        return {"status": "error", "mock": True, "items": [], "error": f"Tool timed out after {timeout:g} seconds."}
    finally:
        # Do not wait for a timed-out provider call before the graph can continue.
        executor.shutdown(wait=False, cancel_futures=True)


def _simulate_failure(state: dict[str, Any], tool_name: str) -> bool:
    """Read either the all-tools failure switch or a per-tool test switch."""
    configured = state.get("simulate_tool_failures", False)
    if isinstance(configured, dict):
        return bool(configured.get(tool_name, False))
    return bool(configured)


def _internal_search_result(query: str, top_k: int) -> dict[str, Any]:
    """Convert the RAG list result to the same simple shape as external tools."""
    results = search_internal(query, top_k=top_k)
    return {
        "status": "ok" if results else "empty",
        "mock": False,
        "items": list(results),
        "error": None if results else getattr(results, "reason", "No internal results."),
    }


def _call_tool(tool_name: str, query: str, state: dict[str, Any]) -> dict[str, Any]:
    """Call the selected local tool using its existing signature."""
    if tool_name == "search_regulation":
        return _run_with_timeout(
            search_regulation,
            tool_timeout_seconds(),
            query=query,
            simulate_failure=_simulate_failure(state, tool_name),
        )
    if tool_name == "search_news":
        # Focus viral-rumor searches on their distinctive topic words so a broad
        # word like "export" does not pull in unrelated semiconductor coverage.
        supplier_query = next(
            (
                item["name"]
                for item in state.get("impacted_suppliers", [])
                if item.get("name")
                and not any(
                    call.get("target_supplier") == item["name"]
                    and call.get("status") in {"ok", "empty"}
                    for call in state.get("tool_calls", [])
                )
            ),
            None,
        )
        news_query = supplier_query or (
            "viral unverified social report"
            if re.search(r"\b(viral|rumou?r)\b", query, re.I)
            else query
        )
        return _run_with_timeout(
            search_news,
            tool_timeout_seconds(),
            query=news_query,
            simulate_failure=_simulate_failure(state, tool_name),
        )
    if tool_name == "search_internal":
        # Apply the same timeout contract to internal search as to external clients.
        return _run_with_timeout(
            _internal_search_result,
            tool_timeout_seconds(),
            query=query,
            top_k=int(state.get("top_k", 5)),
        )
    raise ValueError(f"Unknown investigator tool: {tool_name}")


def _remove_missing(missing: list[str], phrase: str) -> list[str]:
    """Remove an evidence need once a matching tool returned usable evidence."""
    return [item for item in missing if phrase.casefold() not in item.casefold()]


def investigate_more(state: dict[str, Any]) -> dict[str, Any]:
    """Perform exactly one bounded evidence-gathering action."""
    if not budget_remaining(state):
        return {
            "evidence_gate_result": "stop_with_uncertainty",
            "evidence_limitations": list(state.get("evidence_limitations", []))
            + ["The configured investigation iteration limit was reached."],
        }

    # Think: select a tool from the question and the evidence already collected.
    tool_name, model_call = _choose_tool_with_model(state)
    query = str(state.get("investigation_objective") or state.get("user_query") or "").strip()
    iteration = int(state.get("investigation_iterations", 0)) + 1
    calls = list(state.get("tool_calls", []))
    observations = list(state.get("observations", []))
    errors = list(state.get("errors", []))
    missing = list(state.get("missing_information", []))
    updates: dict[str, Any] = {"investigation_iterations": iteration}
    if model_call:
        updates["model_calls"] = list(state.get("model_calls", [])) + [model_call]

    # Act: retry a failed tool only up to the configured limit.
    result: dict[str, Any] = {"status": "error", "mock": True, "items": [], "error": "Tool was not called."}
    selected_tool = tool_name
    for attempt in range(retry_limit() + 1):
        result = _call_tool(tool_name, query, state)
        supplier_target = next(
            (
                item["name"]
                for item in state.get("impacted_suppliers", [])
                if item.get("name")
                and not any(
                    prior.get("target_supplier") == item["name"]
                    and prior.get("status") in {"ok", "empty"}
                    for prior in calls
                )
            ),
            None,
        ) if tool_name == "search_news" else None
        calls.append({
            "tool": tool_name,
            "status": result["status"],
            "iteration": iteration,
            "attempt": attempt + 1,
            "query": supplier_target or query,
            **({"target_supplier": supplier_target} if supplier_target else {}),
        })
        if result["status"] != "error":
            break
        errors.append(f"{tool_name}: {result.get('error') or 'unknown tool error'}")

    # If the first tool is unavailable, make one graceful attempt with an alternate source.
    if result["status"] == "error" and tool_name != "search_internal":
        selected_tool = "search_news" if tool_name == "search_regulation" else "search_regulation"
        fallback = _call_tool(selected_tool, query, state)
        calls.append({
            "tool": selected_tool,
            "status": fallback["status"],
            "iteration": iteration,
            "attempt": 1,
            "fallback_for": tool_name,
        })
        if fallback["status"] != "error":
            result = fallback
        else:
            result = fallback
            errors.append(f"{selected_tool} fallback: {fallback.get('error') or 'unknown tool error'}")

    # Observe: record the exact result, including empty/error status, for auditability.
    items = list(result.get("items", []))
    observations.append({
        "iteration": iteration,
        "tool": selected_tool,
        "status": result["status"],
        "mock": result.get("mock", False),
        "items": items,
        "error": result.get("error"),
    })
    updates.update({"tool_calls": calls, "observations": observations, "errors": errors})

    # Put each successful observation into the state bucket expected by other agents.
    if selected_tool == "search_regulation" and result["status"] == "ok":
        updates["government_evidence"] = list(state.get("government_evidence", [])) + items
        missing = _remove_missing(missing, "regulatory")
        missing = _remove_missing(missing, "external event")
    elif selected_tool == "search_news" and result["status"] == "ok":
        updates["news_articles"] = list(state.get("news_articles", [])) + items
        missing = _remove_missing(missing, "external event")
        missing = _remove_missing(missing, "secondary reporting")
    elif selected_tool == "search_internal" and result["status"] == "ok":
        updates["internal_documents"] = list(state.get("internal_documents", [])) + items
        missing = _remove_missing(missing, "internal")
    else:
        limitation = f"{selected_tool} returned {result['status']}: {result.get('error') or 'no matching evidence'}"
        updates["evidence_limitations"] = list(state.get("evidence_limitations", [])) + [limitation]
        if result["status"] == "empty":
            missing.append(f"Evidence not found by {selected_tool}")

    updates["missing_information"] = list(dict.fromkeys(missing))
    return updates
