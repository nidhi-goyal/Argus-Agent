"""Serve the ARGUS browser interface on the local machine."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import webbrowser
from urllib.parse import urlsplit

from config.settings import PROJECT_ROOT
from graph.graph import run_investigation


MAX_REQUEST_BYTES = 16_384
MAX_QUESTION_LENGTH = 2_000
WEB_ROOT = PROJECT_ROOT / "web"
ASSETS = {
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/assets/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def _browser_result(state: dict[str, Any]) -> dict[str, Any]:
    """Select the investigation results needed by the browser."""
    scores = {
        "risk": state.get("risk_score", 0),
        "risk_level": state.get("risk_level", "unknown"),
        "impact": state.get("impact_score", 0),
        "probability": state.get("probability_score", 0),
        "urgency": state.get("urgency_score", 0),
        "confidence": state.get("confidence_score", 0),
        "evidence_quality": state.get("evidence_quality_score", 0),
        "formula": state.get("risk_formula", ""),
    }
    evidence: list[dict[str, Any]] = []
    for category, key in (
        ("Government", "government_evidence"),
        ("News and company reports", "news_articles"),
        ("Market", "market_evidence"),
        ("Internal", "internal_documents"),
    ):
        for item in state.get(key, []):
            evidence.append({
                "category": category,
                "source_id": item.get("source_id", item.get("id", "Source")),
                "title": item.get("title", item.get("name", item.get("source_id", "Evidence"))),
                "summary": str(
                    item.get("snippet", item.get("text", item.get("description", "")))
                )[:1_200],
                "date": item.get("date", item.get("published_at", "")),
                "authority": item.get("source_authority", item.get("authority", "")),
            })

    return {
        "report": state.get("final_report", ""),
        "scores": scores,
        "evidence": evidence,
        "claims": state.get("claims", []),
        "conflicts": state.get("conflicting_claims", []),
        "actions": state.get("recommended_actions", []),
        "gate": state.get("evidence_gate_result", ""),
        "iterations": state.get("investigation_iterations", 0),
        "limitations": state.get("evidence_limitations", []),
        "errors": state.get("errors", []),
        "input_allowed": state.get("input_allowed", True),
        "evaluation": state.get("evaluation_result", {}),
    }


class ArgusRequestHandler(BaseHTTPRequestHandler):
    """Serve the static interface and accept same-origin investigation requests."""

    max_iterations = 4

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path in ASSETS:
            filename, content_type = ASSETS[path]
            self._send_file(WEB_ROOT / filename, content_type)
            return
        if path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "Not found."})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/investigate":
            self._send_json(404, {"error": "Not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid request size."})
            return
        if content_length <= 0:
            self._send_json(400, {"error": "Request body is required."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request is too large."})
            return

        try:
            request = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return
        if not isinstance(request, dict):
            self._send_json(400, {"error": "Request body must be a JSON object."})
            return

        question = request.get("question")
        if not isinstance(question, str) or not question.strip():
            self._send_json(400, {"error": "Enter a question to investigate."})
            return
        if len(question) > MAX_QUESTION_LENGTH:
            self._send_json(
                400,
                {"error": f"Question must be {MAX_QUESTION_LENGTH} characters or fewer."},
            )
            return

        try:
            state = run_investigation(
                question.strip(),
                max_investigation_iterations=self.max_iterations,
            )
        except Exception:
            logging.exception("ARGUS browser investigation failed")
            self._send_json(
                500,
                {"error": "The investigation failed. Check the server console for details."},
            )
            return
        self._send_json(200, _browser_result(state))

    def _send_file(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            logging.exception("Could not read browser asset: %s", path)
            self._send_json(500, {"error": "The browser interface asset could not be read."})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def log_message(self, format: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), format % args)


def serve_browser_app(port: int, max_iterations: int) -> int:
    """Run the local-only HTTP server until interrupted."""
    handler = type(
        "ConfiguredArgusRequestHandler",
        (ArgusRequestHandler,),
        {"max_iterations": max_iterations},
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}"
    print(f"ARGUS browser app is running at {url}")
    print("Press Ctrl+C to stop the local server.")
    try:
        if not webbrowser.open(url, new=2):
            logging.warning("Could not open a browser automatically. Visit %s", url)
    except webbrowser.Error:
        logging.exception("Could not open a browser automatically. Visit %s", url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ARGUS browser app.")
    finally:
        server.server_close()
    return 0
