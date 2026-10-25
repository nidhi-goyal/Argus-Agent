"""Tests for the Vercel FastAPI entrypoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api.index as vercel_api


client = TestClient(vercel_api.app)


def test_health_check():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_is_served_by_fastapi_fallback():
    response = client.get("/")

    assert response.status_code == 200
    assert "ARGUS | Risk intelligence" in response.text


def test_investigation_rejects_invalid_question():
    response = client.post("/api/investigate", json={"question": " "})

    assert response.status_code == 400
    assert response.json() == {"error": "Enter a question to investigate."}


def test_investigation_uses_shared_result_shape(monkeypatch):
    monkeypatch.setattr(vercel_api, "_ensure_index", lambda: None)
    monkeypatch.setattr(
        vercel_api,
        "run_investigation",
        lambda question, **options: {
            "final_report": f"Report for {question}",
            "risk_score": 5,
            "input_allowed": True,
        },
    )

    response = client.post("/api/investigate", json={"question": "  Review risk  "})

    assert response.status_code == 200
    assert response.json()["report"] == "Report for Review risk"
    assert response.json()["scores"]["risk"] == 5
