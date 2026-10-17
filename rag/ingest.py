"""orchestrate document loading, chunking, embedding, and persistence."""

# RAG sequence: 4/5 — connect loading, chunking, embedding, and index persistence.
# Input: source-document directory and optional destination index directory.
# Output: number of indexed chunks; the persisted index is ready for retrieval.

from __future__ import annotations

from pathlib import Path

from rag.chunking import chunk_documents
from rag.faiss_store import VectorStore
from rag.loader import load_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "sample_docs"
DEFAULT_INDEX_DIR = PROJECT_ROOT / "data" / "index"


def build_index(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    index_dir: str | Path = DEFAULT_INDEX_DIR,
) -> int:
    """Build and persist the knowledge index; return the number of chunks indexed."""
    # Keep orchestration here; parsing, chunking, and vector storage stay separate.
    documents = load_documents(data_dir)
    if not documents:
        raise ValueError(f"No supported documents found under {data_dir}")
    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError(f"Documents under {data_dir} contained no indexable text")
    # Embed all chunks and persist both their text/metadata and the vector index.
    VectorStore.from_chunks(chunks).save(index_dir)
    return len(chunks)
