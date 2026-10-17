"""metadata-filtered semantic search over internal knowledge."""

# RAG sequence: 5/5 — search the persisted index, apply filters, then rerank results.
# Input: a non-empty query, top_k result limit, and optional metadata/date filters.
# Output: SearchResults containing text, source ID, metadata, and score; an empty result has a reason.

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from rag.faiss_store import load_index
from rag.reranker import is_stale, rerank_chunks


INDEX_DIR = Path(__file__).resolve().parents[1] / "data" / "index"
FILTER_ALIASES = {
    "document_type": "doc_type",
    "type": "doc_type",
    "date": "doc_date",
}


class SearchResults(list[dict[str, Any]]):
    """List-compatible search response with an explicit weak/no-result reason."""

    def __init__(self, values: list[dict[str, Any]], reason: str | None = None):
        super().__init__(values)
        self.reason = reason


def _matches_filters(
    metadata: dict[str, Any],
    filters: dict[str, Any] | None,
    today: date | None = None,
) -> bool:
    if not filters:
        return True
    # Normalize aliases and compare values without case sensitivity.
    for requested_key, expected in filters.items():
        if expected is None:
            continue
        key = FILTER_ALIASES.get(requested_key, requested_key)
        if key == "exclude_stale":
            continue
        actual = metadata.get(key)
        if key in {"date_from", "date_to"}:
            continue
        if key == "doc_date" and isinstance(expected, dict):
            doc_date = str(actual or "")
            if expected.get("from") and doc_date < str(expected["from"]):
                return False
            if expected.get("to") and doc_date > str(expected["to"]):
                return False
            continue
        if isinstance(expected, (list, tuple, set)):
            if str(actual).casefold() not in {str(value).casefold() for value in expected}:
                return False
        elif str(actual or "").casefold() != str(expected).casefold():
            return False
    # Date ranges and stale exclusion are handled separately from exact metadata fields.
    doc_date = str(metadata.get("doc_date", ""))
    if filters.get("date_from") and doc_date < str(filters["date_from"]):
        return False
    if filters.get("date_to") and doc_date > str(filters["date_to"]):
        return False
    if filters.get("exclude_stale") and is_stale(metadata, today=today):
        return False
    return True


def search_internal(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> SearchResults:
    """Return ranked chunks in the agreed result shape; empty results explain why."""
    if not query or not query.strip():
        raise ValueError("query must contain non-whitespace text")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    try:
        store = load_index(INDEX_DIR)
    except FileNotFoundError:
        return SearchResults([], "Internal knowledge index is not built; run rag.ingest.build_index().")

    # Fetch extra candidates so metadata filtering does not leave too few results.
    candidate_count = min(len(store.chunks), max(top_k * 8, top_k))
    candidates: list[dict[str, Any]] = []
    for index, score in store.search(query, candidate_count):
        chunk = store.chunks[index]
        metadata = chunk.get("metadata", {})
        if not _matches_filters(metadata, filters):
            continue
        result = {
            "text": chunk["text"],
            "source_id": chunk["source_id"],
            "metadata": dict(metadata),
            "score": max(0.0, min(1.0, score)),
        }
        candidates.append(result)

    # Drop weak matches explicitly, then use document freshness to refine the order.
    relevant = [item for item in candidates if item["score"] >= 0.12]
    if not relevant:
        reason = "No relevant internal documents matched the query and metadata filters."
        return SearchResults([], reason)
    ranked = rerank_chunks(relevant)
    return SearchResults(ranked[:top_k])
