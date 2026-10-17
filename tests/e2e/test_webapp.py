"""End-to-end tests for the local browser interface."""

from __future__ import annotations

import http.client
import json
import threading

from http.server import ThreadingHTTPServer

import webapp


def test_browser_api_runs_investigation_and_returns_display_data(monkeypatch):
    investigated: list[tuple[str, dict[str, object]]] = []

    def fake_investigation(question: str, **options: object) -> dict[str, object]:
        investigated.append((question, options))
        return {
            "final_report": "Example report",
            "risk_score": 6.25,
            "risk_level": "medium",
            "impact_score": 7.0,
            "probability_score": 5.0,
            "urgency_score": 6.0,
            "confidence_score": 0.75,
            "evidence_quality_score": 0.8,
            "risk_formula": "risk = impact*0.40 + probability*0.35 + urgency*0.25",
            "government_evidence": [
                {"source_id": "NOTICE-1", "title": "Official notice", "snippet": "Notice details"}
            ],
            "recommended_actions": [
                {"action": "Review exposure", "owner": "legal", "requires_human_approval": True}
            ],
            "evidence_gate_result": "pass",
            "investigation_iterations": 2,
            "conflicting_claims": [],
            "input_allowed": True,
        }

    monkeypatch.setattr(webapp, "run_investigation", fake_investigation)
    handler = type(
        "TestArgusRequestHandler",
        (webapp.ArgusRequestHandler,),
        {"max_iterations": 3},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port)

    try:
        body = json.dumps({"question": "  Check supplier exposure  "})
        connection.request(
            "POST",
            "/api/investigate",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read())

        assert response.status == 200
        assert payload["report"] == "Example report"
        assert payload["scores"]["risk"] == 6.25
        assert payload["evidence"][0]["source_id"] == "NOTICE-1"
        assert payload["actions"][0]["owner"] == "legal"
        assert investigated == [
            ("Check supplier exposure", {"max_investigation_iterations": 3})
        ]
    finally:
        connection.close()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_browser_api_rejects_empty_question():
    server = ThreadingHTTPServer(("127.0.0.1", 0), webapp.ArgusRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port)

    try:
        connection.request(
            "POST",
            "/api/investigate",
            body=json.dumps({"question": "  "}),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read())

        assert response.status == 400
        assert payload["error"] == "Enter a question to investigate."
    finally:
        connection.close()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_web_mode_opens_browser_and_stops_cleanly(monkeypatch, capsys):
    opened_urls: list[tuple[str, int]] = []
    closed: list[bool] = []

    class FakeServer:
        def __init__(self, address, _handler):
            self.address = address

        def serve_forever(self):
            raise KeyboardInterrupt

        def server_close(self):
            closed.append(True)

    monkeypatch.setattr(webapp, "ThreadingHTTPServer", FakeServer)
    monkeypatch.setattr(
        webapp.webbrowser,
        "open",
        lambda url, new: opened_urls.append((url, new)) or True,
    )

    assert webapp.serve_browser_app(8123, 4) == 0
    assert opened_urls == [("http://127.0.0.1:8123", 2)]
    assert closed == [True]
    assert "ARGUS browser app is running at http://127.0.0.1:8123" in capsys.readouterr().out
