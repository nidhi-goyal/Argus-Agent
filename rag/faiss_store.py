"""persist local vector indexes, using FAISS when it is installed."""

# RAG sequence: 3/5 — embed text, store vectors, and save or reload the index.
# Input: text chunks to index, a query plus result limit to search, or an index directory to load.
# Output: a VectorStore with ranked (chunk index, similarity score) pairs; saves chunk metadata and vectors.

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from pathlib import Path
from typing import Any


# Each document/query is represented by a fixed-size vector with 512 numeric
# slots. A fixed size lets the vector store compare every piece of text equally.
DIMENSIONS = 512
# Find words and numbers in text; punctuation and whitespace act as separators.
TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
# Common words carry little topic-specific meaning, so search ignores them when
# calculating exact-term overlap (the dense vector still uses all tokens).
STOP_WORDS = {
    "a", "about", "after", "all", "an", "and", "are", "as", "at", "be", "by",
    "did", "do", "does", "for", "from", "has", "have", "how", "in", "into", "is",
    "it", "of", "on", "or", "our", "the", "their", "this", "to", "was", "were",
    "what", "when", "which", "who", "why", "with",
}


def embed_text(text: str) -> list[float]:
    """Turn text into a normalized list of numbers that can be compared in search.
    
    This lightweight feature-hashing approach needs no downloaded AI model. The
    same word always maps to the same vector position, so the same text produces
    the same embedding each time.
    """
    # Start with 512 empty slots; each word will add a small signal to one slot.
    vector = [0.0] * DIMENSIONS
    # Lowercase first so words like "Supplier" and "supplier" are treated equally.
    tokens = TOKEN_PATTERN.findall(text.casefold())
    for token in tokens:
        # A stable hash turns each word into an integer without storing a dictionary
        # of all known words. The integer selects a vector position and sign.
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "little")
        index = value % DIMENSIONS
        vector[index] += 1.0 if (value >> 9) & 1 else -1.0
    # Divide each slot by the vector length. This makes similarity less dependent
    # on how long the original text was.
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def _faiss_module() -> Any | None:
    """Load FAISS only if installed, allowing the project to run without it."""
    try:
        return importlib.import_module("faiss")
    except ModuleNotFoundError as exc:
        if exc.name != "faiss":
            raise
        # The caller can use the built-in exact-search implementation instead.
        return None


class VectorStore:
    """Keep document chunks and embeddings together and search for similar text.

    FAISS is used when selected and available; otherwise vectors are compared
    directly in Python. Both backends return the same result format.
    """

    def __init__(self, chunks: list[dict[str, Any]], vectors: list[list[float]], backend: str):
        # Each text chunk needs one matching numeric vector at the same list index.
        if len(chunks) != len(vectors):
            raise ValueError("Each indexed chunk must have exactly one embedding")
        # Keeping chunks and vectors aligned lets a search score point back to its source.
        self.chunks = chunks
        self.vectors = vectors
        self.backend = backend
        self._faiss_index: Any | None = None
        if backend == "faiss":
            # FAISS is an optional faster search library; fail clearly if an index
            # requests it but the dependency is missing from this environment.
            faiss = _faiss_module()
            if faiss is None:
                raise RuntimeError("The persisted index requires faiss-cpu, which is not installed")
            # Inner-product search compares vectors. Our normalized vectors make
            # the result act like cosine similarity.
            index = faiss.IndexFlatIP(DIMENSIONS)
            if vectors:
                numpy = importlib.import_module("numpy")
                # FAISS expects a two-dimensional array of 32-bit numbers.
                index.add(numpy.asarray(vectors, dtype="float32"))
            self._faiss_index = index
        elif backend != "python-exact":
            # Do not silently accept a typo or an index from an unknown backend.
            raise ValueError(f"Unsupported vector index backend: {backend}")

    @classmethod
    def from_chunks(cls, chunks: list[dict[str, Any]]) -> "VectorStore":
        """Create embeddings for chunks and choose the best available backend."""
        # Convert each chunk's text into a vector, keeping the same order as chunks.
        vectors = [embed_text(chunk["text"]) for chunk in chunks]
        # Selecting the backend here means callers do not need FAISS-specific logic.
        return cls(chunks, vectors, "faiss" if _faiss_module() else "python-exact")

    def search(self, query: str, limit: int) -> list[tuple[int, float]]:
        """Return the best matching chunks as (chunk position, similarity score)."""
        # There is nothing useful to search for if the result limit or index is empty.
        if limit <= 0 or not self.chunks:
            return []
        # Convert the search question into the same type of vector as each chunk.
        query_vector = embed_text(query)
        if self._faiss_index is not None:
            # Ask FAISS for scores against every stored vector. We use all scores
            # because the later lexical ranking combines with these values.
            numpy = importlib.import_module("numpy")
            scores, indexes = self._faiss_index.search(
                numpy.asarray([query_vector], dtype="float32"),
                len(self.chunks),
            )
            dense_scores = {
                int(index): float(score)
                for index, score in zip(indexes[0], scores[0])
                if int(index) >= 0
            }
        else:
            # Portable fallback: calculate the dot product with each stored vector.
            dense_scores = {
                index: sum(left * right for left, right in zip(query_vector, vector))
                for index, vector in enumerate(self.vectors)
            }
        # Also compare actual query words with document words. This helps exact
        # names and short queries, which can be less clear from hashed vectors.
        query_terms = {
            term for term in (token.casefold() for token in TOKEN_PATTERN.findall(query))
            if term not in STOP_WORDS
        }
        # Store each chunk's unique words once; repeated words in one chunk do not
        # make that chunk seem more relevant just because a word was repeated.
        document_terms = [
            {token.casefold() for token in TOKEN_PATTERN.findall(chunk["text"])}
            for chunk in self.chunks
        ]
        # Count how many chunks contain each query word. Words found everywhere
        # are less distinctive than rare words such as a supplier or product name.
        document_frequency = {
            term: sum(term in terms for terms in document_terms)
            for term in query_terms
        }
        weights = {
            term: math.log((len(document_terms) + 1) / (frequency + 1)) + 1.0
            for term, frequency in document_frequency.items()
        }
        # Used to turn the matching-word total into a score between zero and one.
        total_weight = sum(weights.values())
        scored = []
        for index, terms in enumerate(document_terms):
            # Fraction of the query's weighted words that appear in this chunk.
            lexical_score = (
                sum(weight for term, weight in weights.items() if term in terms) / total_weight
                if total_weight else 0.0
            )
            # Ignore negative dense similarity; a negative match should not lower
            # a valid lexical match below zero.
            dense_score = max(0.0, dense_scores.get(index, 0.0))
            # Mix semantic similarity and exact-word matching into one score.
            scored.append((index, min(1.0, 0.45 * dense_score + 0.55 * lexical_score)))
        # Sort highest score first and return only the requested number of results.
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

    def save(self, index_dir: str | Path) -> None:
        """Write chunks and vectors to disk so future runs can reuse the index."""
        target = Path(index_dir)
        # Create the destination folder, including missing parent folders.
        target.mkdir(parents=True, exist_ok=True)
        # Store text, source metadata, vectors, and format details together so
        # the saved index can be checked and reconstructed later.
        manifest = {
            "format_version": 1,
            "backend": self.backend,
            "dimensions": DIMENSIONS,
            "chunks": self.chunks,
            "vectors": self.vectors,
        }
        manifest_path = target / "index.json"
        temporary_path = target / "index.json.tmp"
        # Write to a temporary file first, then replace the old manifest in one step.
        # This helps avoid leaving a half-written index if saving is interrupted.
        temporary_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        temporary_path.replace(manifest_path)
        if self._faiss_index is not None:
            # FAISS needs its own native index file in addition to the JSON manifest.
            faiss = _faiss_module()
            if faiss is None:
                raise RuntimeError("FAISS became unavailable while saving the vector index")
            faiss.write_index(self._faiss_index, str(target / "index.faiss"))


def load_index(index_dir: str | Path) -> VectorStore:
    """Read a saved index from disk and rebuild the search store."""
    target = Path(index_dir)
    manifest_path = target / "index.json"
    # A missing manifest usually means ingestion has not been run yet.
    if not manifest_path.exists():
        raise FileNotFoundError(f"No persisted ARGUS index at {manifest_path}")
    # Read the metadata and embeddings saved by VectorStore.save().
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Reject indexes from a different format or vector size instead of misreading them.
    if manifest.get("format_version") != 1 or manifest.get("dimensions") != DIMENSIONS:
        raise ValueError(f"Unsupported or corrupt ARGUS index manifest: {manifest_path}")
    # Recreate the store from the saved chunks and vectors.
    store = VectorStore(
        chunks=manifest["chunks"],
        vectors=manifest["vectors"],
        backend=manifest["backend"],
    )
    if manifest["backend"] == "faiss":
        # Reopen FAISS's separate binary index file so searches use the same backend.
        faiss_path = target / "index.faiss"
        if not faiss_path.exists():
            raise FileNotFoundError(f"FAISS index file is missing: {faiss_path}")
        faiss = _faiss_module()
        if faiss is None:
            raise RuntimeError("The persisted index requires faiss-cpu, which is not installed")
        store._faiss_index = faiss.read_index(str(faiss_path))
    return store
