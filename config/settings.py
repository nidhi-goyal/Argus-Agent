"""shared, environment-configurable ARGUS settings."""

# Input: optional environment variables for limits and scoring policy.
# Output: one validated Settings object shared by the graph, guardrails, and agents.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Load the documented .env file once so local settings work after setup instructions.
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Validated runtime limits and the transparent risk scoring formula."""

    max_investigation_iterations: int = 4
    top_k: int = 5
    retry_limit: int = 2
    tool_timeout_seconds: float = 10.0
    confidence_threshold: float = 0.75
    minimum_independent_sources: int = 2
    risk_weight_impact: float = 0.40
    risk_weight_probability: float = 0.35
    risk_weight_urgency: float = 0.25
    sample_docs_dir: Path = PROJECT_ROOT / "data" / "sample_docs"
    index_dir: Path = PROJECT_ROOT / "data" / "index"


def _integer(name: str, default: int, minimum: int) -> int:
    """Read an integer setting and reject values outside its safe range."""
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _positive_float(name: str, default: float) -> float:
    """Read a positive number such as a timeout or confidence threshold."""
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _probability(name: str, default: float) -> float:
    """Read a confidence threshold, which must be between zero and one."""
    value = _positive_float(name, default)
    if value > 1.0:
        raise ValueError(f"{name} must not exceed 1.0")
    return value


def get_settings() -> Settings:
    """Build settings from environment variables, using safe defaults."""
    settings = Settings(
        max_investigation_iterations=_integer("ARGUS_MAX_ITERATIONS", 4, 1),
        top_k=_integer("ARGUS_TOP_K", 5, 1),
        retry_limit=_integer("ARGUS_RETRY_LIMIT", 2, 0),
        tool_timeout_seconds=_positive_float("ARGUS_TOOL_TIMEOUT_SECONDS", 10.0),
        confidence_threshold=_probability("ARGUS_CONFIDENCE_THRESHOLD", 0.75),
        minimum_independent_sources=_integer("ARGUS_MINIMUM_SOURCES", 2, 1),
        risk_weight_impact=_positive_float("ARGUS_RISK_WEIGHT_IMPACT", 0.40),
        risk_weight_probability=_positive_float("ARGUS_RISK_WEIGHT_PROBABILITY", 0.35),
        risk_weight_urgency=_positive_float("ARGUS_RISK_WEIGHT_URGENCY", 0.25),
    )
    weight_total = (
        settings.risk_weight_impact
        + settings.risk_weight_probability
        + settings.risk_weight_urgency
    )
    if abs(weight_total - 1.0) > 0.0001:
        raise ValueError("ARGUS risk weights must add up to 1.0")
    return settings


SETTINGS = get_settings()
