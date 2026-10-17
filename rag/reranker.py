"""prioritize relevant current documents over expired knowledge."""

# RAG sequence: 5/5 — final retrieval sub-step, after similarity search and metadata filtering.
# Input: ranked retrieval chunks with scores and optional status/version/date metadata.
# Output: chunks sorted with current documents preferred and stale items explicitly marked.

from __future__ import annotations

from datetime import date
import re
from typing import Any


def is_stale(metadata: dict[str, Any], today: date | None = None) -> bool:
    today = today or date.today()
    status = str(metadata.get("status", "")).casefold()
    # Explicit inactive statuses take precedence over any date fields.
    if status in {"expired", "superseded", "inactive"}:
        return True
    valid_until = str(metadata.get("valid_until", "")).strip()
    if valid_until:
        # Invalid dates are surfaced as data errors instead of silently treated as current.
        try:
            return date.fromisoformat(valid_until) < today
        except ValueError as exc:
            raise ValueError(f"Invalid valid_until date in metadata: {valid_until}") from exc
    return False


def rerank_chunks(
    chunks: list[dict[str, Any]],
    today: date | None = None,
) -> list[dict[str, Any]]:
    """Apply a small recency boost; preserve relevance and disclose stale items."""
    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for original_position, original in enumerate(chunks):
        item = dict(original)
        metadata = dict(item.get("metadata", {}))
        stale = is_stale(metadata, today=today)
        metadata["stale"] = stale
        item["metadata"] = metadata
        score = float(item.get("score", 0.0))
        # Penalize stale records; modestly boost current records and newer versions.
        if stale:
            score *= 0.72
        else:
            score = min(1.0, score + 0.04)
            version = re.search(r"(\d+(?:\.\d+)*)$", str(metadata.get("version", "")))
            if version:
                score = min(1.0, score + min(0.03, float(version.group(1)) * 0.005))
        item["score"] = score
        ranked.append((score, -original_position, item))
    # Preserve original retrieval order as the tie-breaker for equal adjusted scores.
    ranked.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    return [entry[2] for entry in ranked]
