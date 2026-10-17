"""End-to-end CLI tests for single-question and interactive usage."""

from __future__ import annotations

import sys

import app


def test_interactive_cli_repeats_questions_until_exit(monkeypatch, capsys):
    questions = iter(["First question", "", "Second question", "q"])
    investigated: list[str] = []

    monkeypatch.setattr(sys, "argv", ["app.py"])
    monkeypatch.setattr(app, "_ensure_index", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    def fake_investigation(question, **_options):
        investigated.append(question)
        return {"input_allowed": True, "final_report": f"Report for {question}"}

    monkeypatch.setattr(app, "run_investigation", fake_investigation)

    assert app.main() == 0
    output = capsys.readouterr().out
    assert investigated == ["First question", "Second question"]
    assert "Report for First question" in output
    assert "Report for Second question" in output
    assert "Please enter a question" in output
    assert "Exiting ARGUS." in output


def test_interactive_cli_accepts_quit_case_insensitively(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["app.py"])
    monkeypatch.setattr(app, "_ensure_index", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: "  QuIt ")

    def unexpected_investigation(*_args, **_kwargs):
        raise AssertionError("Exit command should not trigger an investigation")

    monkeypatch.setattr(app, "run_investigation", unexpected_investigation)

    assert app.main() == 0
