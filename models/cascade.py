"""OpenAI Responses API adapter for the assignment-scale model cascade."""

from __future__ import annotations

from functools import lru_cache
import os
import time
from typing import Any

from config.models import MODEL_TIERS
from config.settings import SETTINGS  # Loads the project .env before key lookup.


def _api_key() -> str | None:
    """Return the configured OpenAI key without exposing it in state or logs."""
    return os.getenv("ARGUS_API_KEY") or os.getenv("OPENAI_API_KEY")


def models_enabled() -> bool:
    """The local deterministic flow remains active when no key is configured."""
    return bool(_api_key())


@lru_cache(maxsize=1)
def _client(api_key: str):
    from openai import OpenAI

    return OpenAI(
        api_key=api_key,
        timeout=SETTINGS.tool_timeout_seconds,
        max_retries=0,
    )


def call_model(
    tier: str,
    operation: str,
    instructions: str,
    prompt: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Call one configured tier and return output plus cost/latency telemetry.

    Missing credentials skip the call. API errors are returned as telemetry so
    callers can keep using their deterministic fallback.
    """
    api_key = _api_key()
    if not api_key:
        return None, None

    config = MODEL_TIERS[tier]
    started = time.perf_counter()
    try:
        response = _client(api_key).responses.create(
            model=config["model"],
            instructions=instructions,
            input=prompt,
            reasoning={"effort": config["reasoning_effort"]},
            max_output_tokens=1200,
            store=False,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        estimated_cost = (
            input_tokens * config["input_cost_per_million"]
            + output_tokens * config["output_cost_per_million"]
        ) / 1_000_000
        telemetry = {
            "operation": operation,
            "tier": tier,
            "provider": config["provider"],
            "model": config["model"],
            "status": "ok",
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(estimated_cost, 8),
        }
        return str(getattr(response, "output_text", "") or "").strip(), telemetry
    except Exception as exc:
        telemetry = {
            "operation": operation,
            "tier": tier,
            "provider": config["provider"],
            "model": config["model"],
            "status": "error",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "error_type": type(exc).__name__,
        }
        return None, telemetry


def parse_json_object(text: str | None) -> dict[str, Any] | None:
    """Parse a JSON object, tolerating a surrounding Markdown code fence."""
    if not text:
        return None
    import json

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split(chr(10), 1)[-1].rsplit("```", 1)[0].strip()
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(candidate[start:end + 1])
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None
