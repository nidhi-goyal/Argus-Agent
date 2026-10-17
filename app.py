"""command-line entry point for an ARGUS investigation."""

# Input: an optional executive question and development/test switches.
# Output: one or more evidence-grounded reports; without a question, prompt until exit.

from __future__ import annotations

import argparse
from pathlib import Path

from config.settings import SETTINGS
from graph.graph import run_investigation
from rag.ingest import build_index
from webapp import serve_browser_app


def _ensure_index() -> None:
    """Build the local document index once when a fresh checkout needs it."""
    index_manifest = SETTINGS.index_dir / "index.json"
    if not index_manifest.exists():
        print("Building the internal sample-document index...")
        build_index(SETTINGS.sample_docs_dir, SETTINGS.index_dir)


def _run_question(question: str, max_iterations: int, simulate_tool_failures: bool) -> int:
    """Investigate one question, print its report, and return its status code."""
    result = run_investigation(
        question,
        max_investigation_iterations=max_iterations,
        simulate_tool_failures=simulate_tool_failures,
    )
    print(result.get("final_report", "ARGUS completed without producing a report."))
    return 0 if result.get("input_allowed", False) else 2


def _interactive_loop(max_iterations: int, simulate_tool_failures: bool) -> int:
    """Keep accepting investigation questions until the user requests exit."""
    print("ARGUS is ready. Enter a question, or type Exit, Quit, or Q to stop.")
    exit_code = 0
    while True:
        try:
            question = input("\nARGUS> ").strip()
        except EOFError:
            print("\nExiting ARGUS.")
            return exit_code
        except KeyboardInterrupt:
            print("\nExiting ARGUS.")
            return exit_code

        if question.casefold() in {"exit", "quit", "q"}:
            print("Exiting ARGUS.")
            return exit_code
        if not question:
            print("Please enter a question, or type Exit, Quit, or Q to stop.")
            continue

        exit_code = max(
            exit_code,
            _run_question(question, max_iterations, simulate_tool_failures),
        )


def main() -> int:
    """Run one supplied question or start an interactive prompt when none is given."""
    parser = argparse.ArgumentParser(
        description="Investigate a business, supplier, regulatory, or geopolitical risk question."
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Executive question to investigate (omit it to enter interactive mode)",
    )
    parser.add_argument(
        "--simulate-tool-failure",
        action="store_true",
        help="Simulate news/regulatory failures to test safe degradation",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=SETTINGS.max_investigation_iterations,
        help="Maximum evidence-gathering cycles (default: configured setting)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start the browser interface instead of the terminal prompt",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Local browser-interface port when --web is set (default: 8000)",
    )
    args = parser.parse_args()
    if args.max_iterations < 1:
        parser.error("--max-iterations must be at least 1")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    # Build the index before either mode so a fresh checkout works on first use.
    _ensure_index()

    if args.web:
        return serve_browser_app(args.port, args.max_iterations)

    if not args.question:
        return _interactive_loop(args.max_iterations, args.simulate_tool_failure)
    return _run_question(
        " ".join(args.question),
        args.max_iterations,
        args.simulate_tool_failure,
    )


if __name__ == "__main__":
    raise SystemExit(main())
