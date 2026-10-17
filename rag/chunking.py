"""clean documents and attach metadata to retrieval chunks."""

# RAG sequence: 2/5 — prepare loaded documents for embedding and indexing.
# Input: loader document records; chunk size and overlap are optional settings.
# Output: cleaned text chunks, each retaining its source ID and document metadata.

from __future__ import annotations

import re
from typing import Any


def clean_text(text: str) -> str:
    """Tidy extracted document text before it is split into smaller pieces.

    PDF extraction can leave null characters, repeated spaces, and excessive
    blank lines. Cleaning these up makes the text easier to search and chunk.
    """
    # Replace characters that cannot be displayed or searched usefully.
    text = text.replace("\x00", " ")
    
    # Collapse repeated spaces/tabs and long runs of blank lines.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove whitespace from the beginning and end of the whole document.
    return text.strip()


def chunk_document(
    document: dict[str, Any],
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[dict[str, Any]]:
    """Split one loaded document into searchable chunks.

    ``chunk_size`` and ``overlap`` are measured in words, not characters.
    Each returned chunk includes its text, a source ID, and copied metadata.
    """
    # Reject settings that could create empty chunks or an infinite loop.
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    # Clean first so extra whitespace does not waste space in each chunk.
    text = clean_text(str(document["text"]))
    if not text:
        return []

    # Copy the metadata so adding defaults here does not mutate the input document.
    metadata = dict(document.get("metadata", {}))
    filename = str(document["filename"])
    document_id = str(document["document_id"])
    # Give every chunk the same filter fields, even if a source omitted some values.
    for key in ("doc_type", "supplier", "product", "region", "doc_date", "version"):
        metadata.setdefault(key, "")
    metadata["document_id"] = document_id

    # Work with words so chunk lengths are predictable; move forward by the
    # non-overlapping portion each time (for example, 700 words - 100 overlap).
    words = text.split()
    step = chunk_size - overlap
    chunks: list[dict[str, Any]] = []
    # Shared words at chunk boundaries help keep related sentences together.
    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if not chunk_words:
            continue
        # Number each chunk in its source file so retrieved text can be traced back.
        chunks.append({
            "text": " ".join(chunk_words),
            "source_id": f"{filename}#chunk{len(chunks) + 1}",
            "metadata": dict(metadata),
        })
    return chunks


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[dict[str, Any]]:
    """Chunk every loaded document and return one combined list.

    The inner call makes the chunks for one document; the outer loop repeats
    that operation for all documents and combines the results into one list.
    """
    return [
        chunk
        for document in documents
        for chunk in chunk_document(document, chunk_size=chunk_size, overlap=overlap)
    ]
