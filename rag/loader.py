"""load PDF and plain-text internal knowledge documents."""

# RAG sequence: 1/5 — source documents enter the pipeline here.
# Input: a file path or directory containing PDF, TXT, or Markdown documents.
# Output: document records with extracted text, filename, document ID, and metadata.

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}
METADATA_PREFIX = "ARGUS_METADATA:"


def _extract_pdf_text(path: Path) -> str:
    # Import the PDF parser only when needed so TXT/Markdown ingestion stays lightweight.
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF ingestion requires pypdf. Install project dependencies with "
            "`python -m pip install -r requirements.txt`."
        ) from exc

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_document_metadata(text: str, path: Path) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    metadata: dict[str, Any] = {}
    content_start = 0
    # The sample PDFs put a compact JSON metadata record near the start of the file.
    for index, line in enumerate(lines[:12]):
        candidate = line.strip()
        if candidate.startswith(METADATA_PREFIX):
            try:
                parsed = json.loads(candidate[len(METADATA_PREFIX):].strip())
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid ARGUS metadata in {path.name}: {exc}") from exc
            if not isinstance(parsed, dict):
                raise ValueError(f"ARGUS metadata in {path.name} must be a JSON object")
            metadata = parsed
            content_start = index + 1
            break

    # Supply consistent filter fields when a source file omits optional metadata.
    metadata.setdefault("document_id", path.stem)
    metadata.setdefault("doc_type", "unknown")
    metadata.setdefault("supplier", "")
    metadata.setdefault("product", "")
    metadata.setdefault("region", "")
    metadata.setdefault("doc_date", "")
    metadata.setdefault("version", "")
    cleaned = "\n".join(lines[content_start:]).strip()
    return metadata, cleaned


def load_document(path: str | Path) -> dict[str, Any]:
    """Load one supported file as text plus its filename and metadata."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported document type {suffix!r}: {file_path.name}")
    # PDF needs page extraction; text formats can be decoded directly as UTF-8.
    text = _extract_pdf_text(file_path) if suffix == ".pdf" else file_path.read_text(encoding="utf-8")
    metadata, content = _parse_document_metadata(text, file_path)
    if not content:
        raise ValueError(f"No extractable text in document: {file_path}")
    return {
        "text": content,
        "filename": file_path.name,
        "document_id": str(metadata["document_id"]),
        "metadata": metadata,
    }


def load_documents(data_dir: str | Path) -> list[dict[str, Any]]:
    """Load supported files recursively, in stable filename order."""
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Document directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Document path is not a directory: {root}")
    # Recursive, sorted discovery makes ingestion deterministic across runs.
    paths = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES),
        key=lambda path: path.as_posix().casefold(),
    )
    return [load_document(path) for path in paths]
