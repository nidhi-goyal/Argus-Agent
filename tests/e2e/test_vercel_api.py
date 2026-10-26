"""Tests for the Vercel FastAPI entrypoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api.index as vercel_api
from guardrails.injection import check_input


client = TestClient(vercel_api.app)


def test_health_check():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_is_served_by_fastapi_fallback():
    response = client.get("/")

    assert response.status_code == 200
    assert "ARGUS | Risk intelligence" in response.text
    assert "What can ARGUS help you investigate?" in response.text
    assert "Supplier exposure" in response.text
    assert "Trace product exposure" in response.text
    guide = response.text.split('<section class="guide-card"', 1)[1].split("</section>", 1)[0]
    assert 'aria-label="Sample questions you can try"' in guide
    assert guide.count('class="example-chip"') == 5
    assert "TEST AN OFF-TOPIC QUESTION" in guide
    assert "What is a good recipe for chocolate cake?" in guide
    assert check_input("What is a good recipe for chocolate cake?")["allowed"] is False


def test_static_assets_are_served_by_fastapi():
    response = client.get("/assets/styles.css")

    assert response.status_code == 200
    assert "--navy: #101a24" in response.text


def test_favicon_is_served_by_fastapi():
    response = client.get("/favicon.svg")

    assert response.status_code == 200
    assert "<svg" in response.text


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
