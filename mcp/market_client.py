"""mock market intelligence client."""

# ARGUS workflow: optional external market lookup, called during evidence discovery.
# Input: a market symbol, such as a fictional ticker or commodity code.
# Output: clearly labeled mock ToolResult-style response; market data is not implemented yet.


def get_market_signal(symbol: str) -> dict:
    """Return a labeled not-implemented response until the stretch task is built."""
    # A blank symbol is a caller input error, not an empty search result.
    if not symbol.strip():
        raise ValueError("symbol must not be empty")
    # Return the standard status fields so an investigator can handle this stub safely.
    return {"status": "empty", "mock": True, "items": [], "error": "Market mock data is not configured."}
