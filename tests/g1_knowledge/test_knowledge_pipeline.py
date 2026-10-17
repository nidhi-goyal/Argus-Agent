"""ingestion, retrieval quality, metadata, reranking, and external tools."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from agents.internal_analyst import analyze_internal_exposure
from mcp.government_client import search_regulation
from mcp.news_client import search_news
from rag.faiss_store import load_index
from rag.chunking import chunk_document
from rag.ingest import DEFAULT_DATA_DIR, build_index
from rag.loader import load_documents
from rag.reranker import rerank_chunks
from rag.retrieval import search_internal


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "evaluation" / "datasets" / "g1_retrieval_qa.json"


@pytest.fixture(scope="module", autouse=True)
def indexed_sample_documents():
    build_index()


def test_dataset_has_at_least_ten_grounded_prompts():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    assert len(dataset) >= 10
    assert all(item["prompt"] and item["expected_source"] and item["expected_fact"] for item in dataset)


def test_retrieval_precision_over_labeled_prompt_set_exceeds_eighty_percent():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    hits = 0
    for item in dataset:
        results = search_internal(item["prompt"], top_k=5)
        hits += any(result["source_id"].startswith(item["expected_source"] + "#") for result in results)
    precision = hits / len(dataset)
    assert precision > 0.80, f"Expected >0.80 retrieval precision, got {precision:.3f}"


def test_unrelated_query_returns_empty_results_with_reason():
    results = search_internal("quantum archaeology lunar opera", top_k=5)
    assert not results
    assert results.reason


def test_expired_document_is_marked_stale_and_new_contract_ranks_first():
    results = search_internal(
        "Kestrel Components expired contract replacement active contract version",
        top_k=8,
    )
    versions = [result for result in results if result["source_id"].startswith("kestrel_contract")]
    assert len(versions) == 2
    assert versions[0]["source_id"].startswith("kestrel_contract_v2.pdf#")
    expired = next(result for result in versions if "v1_expired" in result["source_id"])
    assert expired["metadata"]["stale"] is True


def test_metadata_filters_limit_results_to_requested_supplier_and_document_type():
    results = search_internal(
        "agreement supplier delivery contract",
        top_k=10,
        filters={"supplier": "Cirrus Silicon", "document_type": "contract"},
    )
    assert results
    assert all(result["metadata"]["supplier"] == "Cirrus Silicon" for result in results)
    assert all(result["metadata"]["doc_type"] == "contract" for result in results)


def test_metadata_date_filter_is_applied():
    results = search_internal(
        "inventory accelerator Helios Edge",
        top_k=10,
        filters={"date_from": "2026-08-01", "date_to": "2026-08-31"},
    )
    assert results
    assert all("2026-08-01" <= result["metadata"]["doc_date"] <= "2026-08-31" for result in results)


def test_ingestion_attaches_source_and_required_metadata_and_index_reloads(tmp_path):
    documents = load_documents(DEFAULT_DATA_DIR)
    assert len(documents) == 8
    count = build_index(DEFAULT_DATA_DIR, tmp_path)
    store = load_index(tmp_path)
    assert count == len(store.chunks) == 8
    assert all(chunk["source_id"] and chunk["metadata"]["document_id"] for chunk in store.chunks)
    assert all(
        {"doc_type", "supplier", "product", "region", "doc_date", "version"} <= set(chunk["metadata"])
        for chunk in store.chunks
    )
    assert store.search("Cirrus Silicon Helios Edge", 1)


def test_long_documents_split_into_overlapping_metadata_preserving_chunks():
    document = {
        "text": " ".join(f"token{index}" for index in range(30)),
        "filename": "long.txt",
        "document_id": "long-document",
        "metadata": {"doc_type": "policy", "supplier": "Cirrus Silicon"},
    }
    chunks = chunk_document(document, chunk_size=10, overlap=2)
    assert len(chunks) == 4
    assert all(chunk["metadata"]["supplier"] == "Cirrus Silicon" for chunk in chunks)
    assert all(chunk["source_id"].startswith("long.txt#chunk") for chunk in chunks)


def test_news_tool_success_empty_and_failure_are_distinct_and_mock_labeled():
    success = search_news("semiconductor export accelerator")
    empty = search_news("unicorn submarine chocolate")
    failure = search_news("semiconductor export", simulate_failure=True)
    assert success["status"] == "ok"
    assert all(item["mock"] is True for item in success["items"])
    assert empty["status"] == "empty" and empty["items"] == []
    assert failure["status"] == "error" and failure["error"]


def test_generic_supplier_disruption_query_does_not_match_unrelated_news():
    result = search_news(
        "I heard there may be a new supplier disruption, but I don't know which supplier. "
        "What can you verify, and what remains unknown?"
    )
    assert result["status"] == "empty"
    assert result["items"] == []


def test_regulation_tool_success_empty_and_failure_are_distinct():
    success = search_regulation("semiconductor export accelerator", jurisdiction="North America")
    empty = search_regulation("unicorn submarine chocolate")
    failure = search_regulation("semiconductor export", simulate_failure=True)
    assert success["status"] == "ok"
    assert all(item["mock"] is True for item in success["items"])
    assert empty["status"] == "empty" and empty["items"] == []
    assert failure["status"] == "error" and failure["error"]


def test_generic_supplier_disruption_query_does_not_match_unrelated_regulations():
    result = search_regulation(
        "I heard there may be a new supplier disruption, but I don't know which supplier. "
        "What can you verify, and what remains unknown?"
    )
    assert result["status"] == "empty"
    assert result["items"] == []


def test_mock_data_contains_seeded_duplicate_false_report_conflict_and_supplier_statement():
    news = json.loads((PROJECT_ROOT / "data" / "mock" / "news.json").read_text(encoding="utf-8"))
    regulations = json.loads((PROJECT_ROOT / "data" / "mock" / "regulations.json").read_text(encoding="utf-8"))
    assert any(item.get("duplicate_of") for item in news)
    assert any("unverified viral" in item["snippet"].casefold() for item in news)
    assert any("immediately" in item["snippet"].casefold() for item in news)
    assert any("unaffected" in item["snippet"].casefold() for item in news)
    assert any("2026-09-01" in item["snippet"] for item in regulations)


def test_internal_analyst_scopes_exposure_to_supplier_and_affected_product():
    updates = analyze_internal_exposure({
        "user_query": "Investigate semiconductor export restrictions and Northstar exposure",
        "government_evidence": [{
            "title": "MOCK advanced accelerator export restrictions",
            "snippet": "Controls apply to advanced accelerator semiconductor categories.",
        }],
    })
    suppliers = {item["name"] for item in updates["impacted_suppliers"]}
    products = {item["name"] for item in updates["impacted_products"]}
    assert suppliers == {"Cirrus Silicon"}
    assert products == {"Helios Edge"}
    assert all(item["source_ids"] for item in updates["impacted_products"])
    assert any("procurement_inventory_note.pdf" in item["source_id"] for item in updates["internal_documents"])


def test_reranker_boosts_current_and_discloses_expired_metadata():
    ranked = rerank_chunks([
        {"text": "same relevance", "source_id": "old", "score": 0.9,
         "metadata": {"status": "expired", "valid_until": "2025-12-31"}},
        {"text": "same relevance", "source_id": "new", "score": 0.9,
         "metadata": {"status": "active", "valid_until": "2027-12-31"}},
    ], today=date(2026, 10, 12))
    assert ranked[0]["source_id"] == "new"
    assert ranked[1]["metadata"]["stale"] is True


def test_tool_inputs_reject_empty_queries():
    with pytest.raises(ValueError):
        search_news(" ")
    with pytest.raises(ValueError):
        search_regulation("")
    with pytest.raises(ValueError):
        search_internal(" ", top_k=3)
