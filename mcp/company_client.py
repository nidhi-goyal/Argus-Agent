"""mock company intelligence client."""

# ARGUS workflow: optional external company lookup, called during evidence discovery.
# Input: a company name to look up.
# Output: clearly labeled mock ToolResult-style response; company data is not implemented yet.


def company_profile(company: str) -> dict:
    """Return a labeled not-implemented response until the stretch task is built."""
    # Reject blank names so callers do not mistake an invalid request for no matches.
    if not company.strip():
        raise ValueError("company must not be empty")
    # Keep the result shape explicit while the optional company-data source is unbuilt.
    return {"status": "empty", "mock": True, "items": [], "error": "Company mock data is not configured."}
