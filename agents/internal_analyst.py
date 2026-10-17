"""identify supplier/product exposure from retrieved internal evidence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rag.retrieval import search_internal


TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _event_component_matches(component: str, event_text: str) -> bool:
    component_terms = {term.casefold() for term in TOKEN_PATTERN.findall(component)}
    event_terms = {term.casefold() for term in TOKEN_PATTERN.findall(event_text)}
    specific_terms = component_terms - {"c", "x", "r", "lf", "controller", "silicon", "component"}
    if "accelerator" in event_terms:
        return "accelerator" in specific_terms
    if "gpu" in event_terms or "graphics" in event_terms:
        return bool(specific_terms & {"gpu", "graphics", "accelerator"})
    if "semiconductor" in event_terms or "semiconductors" in event_terms:
        return bool(specific_terms & {"accelerator", "semiconductor", "chip"})
    return bool(specific_terms & event_terms)


def analyze_internal_exposure(state: dict[str, Any]) -> dict[str, Any]:
    """Return only state updates owned by the internal exposure analyst."""
    query = str(state.get("investigation_objective") or state.get("user_query") or "").strip()
    if not query:
        raise ValueError("state must include a non-empty user_query or investigation_objective")
    external_text = " ".join(
        str(item.get(field, ""))
        for key in ("news_articles", "government_evidence", "market_evidence")
        for item in state.get(key, [])
        for field in ("title", "snippet", "text")
    )
    retrieval_query = f"{query} {external_text}".strip()
    documents = search_internal(retrieval_query, top_k=int(state.get("top_k", 8)))
    event_terms = {term.casefold() for term in TOKEN_PATTERN.findall(external_text or query)}
    mapping_query = next(
        (
            term for term in ("accelerator", "gpu", "graphics", "semiconductor", "chip")
            if term in event_terms
        ),
        external_text or query,
    )
    mapping_chunks = search_internal(
        mapping_query,
        top_k=20,
        filters={"doc_type": "product_mapping"},
    )
    suppliers: dict[str, set[str]] = {}
    products: dict[str, set[str]] = {}
    mappings: list[tuple[str, str, str, str]] = []
    for chunk in mapping_chunks:
        for match in re.finditer(
            r"Supplier:\s*(.*?)\s*\|\s*Component:\s*(.*?)\s*\|\s*Products?:\s*(.*?)(?=\.|Supplier:|$)",
            chunk["text"],
            re.IGNORECASE,
        ):
            supplier, component, product_names = (part.strip() for part in match.groups())
            if not _event_component_matches(component, external_text or query):
                continue
            source_id = str(chunk["source_id"])
            for product in re.split(r"\s+and\s+|,\s*", product_names):
                product = product.strip()
                if product:
                    suppliers.setdefault(supplier, set()).add(source_id)
                    products.setdefault(product, set()).add(source_id)
                    mappings.append((supplier, component, product, source_id))

    supporting_documents: list[dict[str, Any]] = []
    for supplier in suppliers:
        supplier_products = [
            product for mapped_supplier, _, product, _ in mappings
            if mapped_supplier == supplier
        ]
        related = search_internal(
            f"{supplier} {' '.join(supplier_products)}",
            top_k=5,
            filters={"supplier": supplier},
        )
        for document in related:
            if any(product in document["text"] for product in products):
                supporting_documents.append(document)
                for item in products.values():
                    item.add(str(document["source_id"]))
                suppliers[supplier].add(str(document["source_id"]))

    internal_documents: list[dict[str, Any]] = []
    for document in [*documents, *supporting_documents, *mapping_chunks]:
        if all(existing["source_id"] != document["source_id"] for existing in internal_documents):
            internal_documents.append(document)

    return {
        "internal_documents": internal_documents,
        "impacted_suppliers": [
            {"name": name, "source_ids": sorted(source_ids)}
            for name, source_ids in sorted(suppliers.items())
        ],
        "impacted_products": [
            {"name": name, "source_ids": sorted(source_ids)}
            for name, source_ids in sorted(products.items())
        ],
        "missing_information": (
            [] if mappings else ["No product/component mapping matched the external event scope"]
        ),
    }
