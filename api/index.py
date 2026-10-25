"""Vercel API routes for the ARGUS browser interface."""

from __future__ import annotations

import json
import logging
from threading import Lock
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config.settings import PROJECT_ROOT, SETTINGS
from graph.graph import run_investigation
from rag.ingest import build_index
from webapp import MAX_QUESTION_LENGTH, MAX_REQUEST_BYTES, _browser_result


app = FastAPI()
_index_lock = Lock()
FRONTEND_ROOT = PROJECT_ROOT / "public"


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_ROOT / "index.html", media_type="text/html")


def _ensure_index() -> None:
    """Build the internal-document index in writable function storage once."""
    manifest = SETTINGS.index_dir / "index.json"
    if manifest.exists():
        return
    with _index_lock:
        if not manifest.exists():
            build_index(SETTINGS.sample_docs_dir, SETTINGS.index_dir)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/investigate")
async def investigate(request: Request) -> JSONResponse:
    content_length = request.headers.get("content-length", "0")
    try:
        request_size = int(content_length)
    except ValueError:
        return JSONResponse({"error": "Invalid request size."}, status_code=400)
    if request_size <= 0:
        return JSONResponse({"error": "Request body is required."}, status_code=400)
    if request_size > MAX_REQUEST_BYTES:
        return JSONResponse({"error": "Request is too large."}, status_code=413)

    body = await request.body()
    if len(body) > MAX_REQUEST_BYTES:
        return JSONResponse({"error": "Request is too large."}, status_code=413)
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            {"error": "Request body must be valid JSON."},
            status_code=400,
        )
    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "Request body must be a JSON object."},
            status_code=400,
        )

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return JSONResponse(
            {"error": "Enter a question to investigate."},
            status_code=400,
        )
    if len(question) > MAX_QUESTION_LENGTH:
        return JSONResponse(
            {"error": f"Question must be {MAX_QUESTION_LENGTH} characters or fewer."},
            status_code=400,
        )

    try:
        _ensure_index()
        state: dict[str, Any] = run_investigation(
            question.strip(),
            max_investigation_iterations=SETTINGS.max_investigation_iterations,
        )
    except Exception:
        logging.exception("ARGUS Vercel investigation failed")
        return JSONResponse(
            {"error": "The investigation failed. Check the function logs for details."},
            status_code=500,
        )
    return JSONResponse(_browser_result(state))


app.mount("/", StaticFiles(directory=FRONTEND_ROOT, html=True), name="frontend")
