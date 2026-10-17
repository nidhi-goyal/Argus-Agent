# ARGUS — Autonomous Risk & Global Unified Surveillance

ARGUS is a personal project exploring how an AI research assistant can investigate geopolitical, regulatory, supply-chain, and market events. It retrieves organization-specific context, checks claim provenance and contradictions, assesses risk, and suggests actions for human review.

The sample company, supplier, product, regulatory, and news information in `data/` is fictional and used for testing. External-tool results are marked `mock: true`; they are not live intelligence.

## Project structure

| Path | Purpose |
|---|---|
| `rag/` | Document loading, chunking, indexing, and retrieval |
| `mcp/` | Mock news and government search clients |
| `agents/` | Investigation, analysis, verification, risk, and recommendations |
| `graph/`, `models/`, `config/` | Workflow, data schemas, and settings |
| `guardrails/` | Input safety, evidence checks, and research budgets |
| `data/` | Fictional internal documents and external data |
| `evaluation/` | Quality metrics and repeatable regression benchmark |
| `tests/` | Component and end-to-end scenario tests |

## Setup

Python 3.11 or newer is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The retrieval pipeline uses deterministic local feature vectors. The investigation also keeps a deterministic local path; setting `ARGUS_API_KEY` in `.env` enables the optional OpenAI cascade for query planning, tool choice, and evidence review. When `faiss-cpu` is available, the persisted vector index uses FAISS `IndexFlatIP`; otherwise it uses an exact, dependency-free local index with the same retrieval contract. External news and regulatory sources remain mock data.

Build or reload the local index:

```powershell
python -c "from rag.ingest import build_index; build_index()"
```

Run an investigation from the command line:

```powershell
python app.py "There are reports of new semiconductor export restrictions. Investigate what changed, check whether our suppliers/products may be exposed, estimate risk and recommend next actions."
```

Start the browser interface with `python app.py --web`, then open `http://127.0.0.1:8000`. Enter a question to review the report, risk dimensions, evidence, conflicts, and suggested actions. The local server listens only on this computer. Press Ctrl+C in the terminal to stop it; use `python app.py --web --port 8080` to select another port. The browser interface uses the same mock external-data workflow. When `ARGUS_API_KEY` is configured, model calls are included in the investigation; recommendations are never executed.

Run without a question to start an interactive session. Enter questions repeatedly; type `Exit`, `Quit`, or `Q` to end it. The app builds the local retrieval index on first run. Use `--simulate-tool-failure` to exercise tool errors and safe degradation.

## Tests and evaluation

Run the test suite:

```powershell
python -m pytest -q
```

Run the labeled regression benchmark:

```powershell
python -m evaluation.regression
```

## Optional OpenAI model cascade

Set `ARGUS_API_KEY` in `.env` to enable the configured tiers in `config/models.py`. ARGUS uses the small tier for query planning and tool choice, medium for routine claim review, and higher reasoning effort for conflicting or date-sensitive evidence. The verifier filters evidence locally and caps model input at ten relevant excerpts. The final report lists model, latency, token usage, and estimated cost. Without a key, the deterministic local workflow runs as before.

## Sample data

- The fictional company is **Northstar Instruments**.
- **Cirrus Silicon** supplies the controlled advanced accelerator used only by **Helios Edge**; other products do not depend on Cirrus.
- Current and expired/replacement agreements are included. Retrieval marks expired material stale and boosts its newer replacement.
- Mock regulatory evidence limits controls to defined advanced accelerator categories and lists an effective date of **2026-09-01**.
- Mock secondary reports include repeated copies, a conflicting immediate effective date, an unverified viral claim, and a Cirrus statement that deliveries are unaffected. All are labeled MOCK.

## Browser workflow examples

Use these questions to exercise different paths through the fictional corpus. The sample data is not live intelligence.

- **Unsupported event:** “I heard there may be a new supplier disruption, but I don't know which supplier. What can you verify, and what remains unknown?” Expected: no matching external event evidence; unrelated export-control notices should not be presented.
- **Regulatory scope and conflicting date:** “When do the new semiconductor export controls take effect? Compare the official notice with industry reports and explain any disagreement.” Expected: cite the official 2026-09-01 date and disclose the unverified immediate-effect claim.
- **Viral misinformation:** “Is the viral claim that all consumer electronics exports are banned supported by authoritative evidence?” Expected: label the claim unverified and distinguish it from the narrower official notice.
- **Supplier assurance and exposure:** “Cirrus Silicon says committed deliveries are unaffected. Does that confirm Helios Edge is outside the export controls?” Expected: distinguish delivery assurance from legal product coverage and identify the possible mapping.
- **Inventory and continuity:** “How much Helios Edge accelerator inventory do we have, and what should operations verify before making a continuity decision?” Expected: retrieve the fictional 45-day inventory note and recommend human-reviewed follow-up.
- **Current agreement:** “What is the current Kestrel Components contract, and has an older agreement been replaced?” Expected: rank active contract v2 above expired v1 and mark the old version stale.
- **Internal mapping:** “Which Northstar product uses the advanced accelerator supplied by Cirrus Silicon?” Expected: map Cirrus Silicon to Helios Edge without claiming other products are affected.

## Risk scoring and guardrails

Risk is a weighted average on a 1–10 scale: `impact * 0.40 + probability * 0.35 + urgency * 0.25`. Change weights and limits with the placeholders in `.env.example`; the weights must add to 1. Evidence confidence and quality are separate scores. The workflow has a bounded research loop, reports tool failures and unresolved conflicts, flags prompt-injection-like text in evidence, and labels supplier, procurement, and legal actions for human review.
