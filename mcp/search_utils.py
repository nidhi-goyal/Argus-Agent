"""Shared query-term normalization for the local mock search clients."""

from __future__ import annotations

import re


SEARCH_STOP_WORDS = frozenset({
    "a", "about", "an", "and", "are", "as", "at", "be", "been", "but",
    "by", "can", "could", "did", "do", "does", "for", "from", "get",
    "has", "have", "how", "i", "if", "in", "into", "is", "it", "its",
    "may", "me", "my", "new", "of", "on", "or", "our", "please", "should",
    "that", "the", "their", "there", "these", "this", "those", "to", "us",
    "was", "we", "were", "what", "when", "where", "which", "who", "why",
    "will", "with", "would", "you", "your", "company", "business", "event",
    "investigate", "question", "reports", "report", "verify", "verified",
    "unknown", "unknowns", "remains", "remain", "available", "evidence",
    "supplier", "suppliers",
})


def search_terms(query: str) -> set[str]:
    """Extract meaningful query terms, excluding generic prompt and business words."""
    return {
        term.casefold()
        for term in re.findall(r"[a-z0-9]+", query, re.IGNORECASE)
        if len(term) > 2 and term.casefold() not in SEARCH_STOP_WORDS
    }
