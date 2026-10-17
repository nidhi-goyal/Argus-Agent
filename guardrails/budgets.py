"""hard limits for investigation loops, retries, and tool time."""

# Input: current shared state and optional configuration limits.
# Output: budget_remaining decision; tools are never retried without a cap.

from __future__ import annotations

from typing import Any

from config.settings import SETTINGS


def budget_remaining(state: dict[str, Any]) -> bool:
    """Return whether another research cycle is allowed."""
    # Each graph loop increments this counter before calling a tool.
    iterations = int(state.get("investigation_iterations", 0))
    limit = int(state.get("max_investigation_iterations", SETTINGS.max_investigation_iterations))
    return iterations < limit


def retry_limit() -> int:
    """Return the configured maximum number of additional attempts per tool."""
    return SETTINGS.retry_limit


def tool_timeout_seconds() -> float:
    """Return the configured timeout used by the investigator's tool runner."""
    return SETTINGS.tool_timeout_seconds

