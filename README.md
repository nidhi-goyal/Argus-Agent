# ARGUS — Autonomous Risk & Global Unified Surveillance

ARGUS investigates geopolitical, regulatory, supply-chain, and market events;
retrieves organization-specific context; checks claim provenance and
contradictions; assesses risk; and suggests human-reviewed actions. This
checkout implements Group 1's knowledge and mock tool layer, Group 2's
LangGraph orchestration/investigation/verifier, and Group 3's guardrails,
scoring, recommendations, reporting, and regression evaluation.

All sample company, supplier, product, regulatory, and news information in
`data/` is invented for testing. External-tool results always carry `mock: true`;
they are not live intelligence.

## Project map

| Path | Purpose | Owner |
|---|---|---|
| `rag/` | PDF/text loading, metadata-aware chunks, indexing and retrieval | Group 1 |
| `mcp/` | Mock news and government search clients | Group 1 |
| `agents/internal_analyst.py` | RAG-based supplier and product exposure mapping | Group 1 |
| `data/sample_docs/` | Fictional internal PDF corpus | Group 1 |
| `data/mock/` | Clearly labeled fictional external data | Group 1 |
| `tests/g1_knowledge/` | Group 1 component tests | Group 1 |
| `evaluation/datasets/g1_retrieval_qa.json` | Retrieval prompts and expected facts | Group 1 |
| `graph/`, `models/`, `config/`, `agents/` | State/schemas, LangGraph workflow, agents, risk, and report | Groups 2/3 |
| `guardrails/` | Input safety, evidence gate, and research budgets | Group 3 |
| `evaluation/datasets/` | Labeled retrieval, orchestration, and trust/quality examples | All groups |
| `evaluation/` | Quality metrics and repeatable regression benchmark | Group 3 |
| `tests/g2_orchestration/`, `tests/g3_trust_quality/`, `tests/e2e/` | Component and integrated scenario tests | Groups 2/3/all |

## Setup

Python 3.11 or newer is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The Group 1 pipeline uses deterministic local feature vectors and has no model
or API-key requirement. When `faiss-cpu` is available, the persisted vector
index uses FAISS `IndexFlatIP`; otherwise it uses an exact, dependency-free
local index with the same retrieval contract. The requirements include the
provided AI-provider and machine-learning libraries, although the current
sample workflow uses mock external data and does not call live providers.

Build/reload the local index:

```powershell
python -c "from rag.ingest import build_index; build_index()"
```

Run the command-line agent for one question:

```powershell
python app.py "There are reports of new semiconductor export restrictions. Investigate what changed, check whether our suppliers/products may be exposed, estimate risk and recommend next actions."
```

Start the browser interface instead:

```powershell
python app.py --web
```

Open `http://127.0.0.1:8000` in a browser, enter an investigation question, and
review the report, risk dimensions, evidence, conflicts, and recommended
actions. The local server only listens on this computer; press Ctrl+C in the
terminal to stop it. Use `python app.py --web --port 8080` to choose a different
port. The browser interface uses the same local mock-data workflow as the
terminal app; it does not call live providers or execute recommendations.

Run without a question to start an interactive session. Enter questions
repeatedly; type `Exit`, `Quit`, or `Q` (case-insensitive) to end the session.

The app builds the local RAG index on first run. Use
`--simulate-tool-failure` to exercise explicit tool errors and safe degradation.
These tools read fictional mock data only; the program does not call live
providers, execute recommendations, or make legal/business decisions.

Run tests for all groups and integration:

```powershell
python -m pytest -q
```

Run the labeled regression benchmark:

```powershell
python -m evaluation.regression
```

Run just one group with `python -m pytest tests/g1_knowledge -q`,
`tests/g2_orchestration`, or `tests/g3_trust_quality`.

## Group 1 data facts

- The fictional company is **Northstar Instruments**.
- **Cirrus Silicon** supplies the controlled advanced accelerator used only
  by **Helios Edge**; other products do not depend on Cirrus.
- Current and expired/replacement agreements are both included. Retrieval
  marks expired material stale and boosts its newer replacement.
- Mock regulatory evidence limits controls to defined advanced accelerator
  categories and lists an effective date of **2026-09-01**.
- Mock secondary reports include repeated copies, a conflicting immediate
  effective date, an unverified viral claim, and a Cirrus statement claiming
  deliveries are unaffected. All are labeled MOCK.

## Browser workflow test questions

Use these questions in the browser to exercise different paths through the
seeded fictional corpus. The sample data is not live intelligence.

- **Unsupported event / safe uncertainty:** “I heard there may be a new
  supplier disruption, but I don't know which supplier. What can you verify,
  and what remains unknown?” Expected: no matching external event evidence;
  unrelated export-control notices should not be presented.
- **Official regulatory scope and conflicting date:** “When do the new
  semiconductor export controls take effect? Compare the official notice with
  industry reports and explain any disagreement.” Expected: cite the official
  2026-09-01 date and disclose the unverified immediate-effect claim.
- **Viral misinformation:** “Is the viral claim that all consumer electronics
  exports are banned supported by authoritative evidence?” Expected: label the
  claim unverified and distinguish it from the narrower official notice.
- **Supplier assurance versus exposure:** “Cirrus Silicon says committed
  deliveries are unaffected. Does that confirm Helios Edge is outside the
  export controls?” Expected: preserve the distinction between delivery
  assurance and legal product coverage; identify the possible mapping.
- **Inventory and continuity:** “How much Helios Edge accelerator inventory
  do we have, and what should operations verify before making a continuity
  decision?” Expected: retrieve the fictional 45-day inventory note and
  recommend human-reviewed follow-up.
- **Current versus expired agreement:** “What is the current Kestrel Components
  contract, and has an older agreement been replaced?” Expected: rank active
  contract v2 above expired v1 and mark the old version stale.
- **Targeted internal mapping:** “Which Northstar product uses the advanced
  accelerator supplied by Cirrus Silicon?” Expected: map Cirrus Silicon to
  Helios Edge without claiming other products are affected.

## Risk scoring and guardrails

Risk is a weighted average on a 1–10 scale:
`impact * 0.40 + probability * 0.35 + urgency * 0.25`. Change weights and
limits with the placeholders in `.env.example`; the weights must add to 1.
Evidence confidence and quality are separate scores. The graph has a bounded
research loop, reports tool failures and unresolved conflicts, flags
prompt-injection-like text in evidence, and labels supplier/procurement/legal
actions for human approval.
