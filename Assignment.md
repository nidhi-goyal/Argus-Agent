# ARGUS Agentic AI — Live Class Assignment Plan (Divided into 3-Groups)...

ARGUS (Autonomous Risk & Global Unified Surveillance Agent): an agent that combines external intelligence with internal company context, verifies evidence, identifies contradictions, scores risk/confidence, and recommends actions.

This plan splits the class into **three groups**. The whole project is broken into **16 sequenced Activities**, each made of clear Tasks. Every Activity and every repository file (using the folder layout from **Section 27 – Suggested Project Structure** of the ARGUS use-case brief) has exactly one owning group

---

## 1. Groups and Members

20 students are divided into 3 groups of near-equal size (7 / 7 / 6).

### Group 1 — Knowledge Builders (RAG + External Intelligence)  ·  7 members

1. Nidhi Mittal
2. Jitendra Kumar Saroj
3. Vivek Harle
4. Aditya Venkata Satyanarayana Mokkapati
5. Radharapu Bharath Kumar
6. Avinash Dupaguntla
7. Raviraj Deshpande


**Mission:** Give ARGUS its *knowledge*: the internal FAISS knowledge base (training data, ingestion, retrieval) and the external intelligence tool layer (news, government/regulatory, market and company tools).

### Group 2 — Agent Orchestrators (LangGraph + Agents)  ·  7 members

1. Kailas Kanade
2. Sheetal Deshpande
3. Vishal Kailas Kharade
4. Usama Mirkar
5. Hariharan
6. Harmeet Bedi
7. Valathappan Sivaraman

**Mission:** Give ARGUS its *brain*: the shared state/schemas, the LangGraph workflow and routing, the supervisor, the ReAct news investigator and the claim verifier/contradiction detector. This group also owns the repository skeleton and the final integration entry point (`app.py`).

### Group 3 — Trust & Quality Guardians (Guardrails + Risk + Evaluation)  ·  6 members

1. Balaji Kumar
2. Surendran Sundarababu
3. Mohit Luthra
4. Shirish Suryakant Pathak
5. Bhanupriya
6. Jolly Shringi

**Mission:** Make ARGUS *safe, decision-ready and measurable*: project setup docs, guardrails and evidence gate, risk scoring and recommendations (with human-approval flag), the evaluator and final report, and the evaluation/regression framework.

> **Note on grouping:** the split follows the class-list order so it is easy to read out. 

### Workload balance at a glance

| | Group 1 — Knowledge | Group 2 — Orchestrators | Group 3 — Trust & Quality |
|---|---|---|---|
| Members | 7 | 7 | 6 |
| Lead activities | A4, A5, A6, A7 | A1, A3, A8, A9, A10 | A2, A11, A12, A13 |
| Component test activity | A14 (RAG & tools) | A14 (graph & agents) | A14 (guardrails, risk, eval) |
| Joint activities | A15 Integration, A16 Scenario testing & demo (all groups, Group 2 leads) | | |
| Section 27 areas owned | `rag/`, `mcp/`, `agents/internal_analyst.py` | `graph/`, `agents/` (supervisor, news_investigator, verifier), `app.py`, `config/`, `models/` | `guardrails/`, `evaluation/`, `agents/` (risk_analyst, recommender, evaluator) |

---

## 2. Activity Roadmap (Sequenced)

Activities are ordered by dependency. A *phase* is a set of activities that can run at the same time.

| # | Activity | Owner | Phase | Needs first | Time-box |
|---|---|---|---|---|---:|
| A1 | Create repository and repository structure | Group 2 (all clone) | 0 – Foundation | — | 10 min |
| A2 | Basic project setup (README, requirements, env template) | Group 3 | 0 – Foundation | A1 | 15 min |
| A3 | Shared contract: state, schemas, settings and stub interfaces | Group 2 (input from all) | 0 – Foundation | A1 | 20 min |
| A4 | Prepare internal training data and mock external data | Group 1 | 0 – Foundation (starts at minute 0) | — | 15 min |
| A5 | Build the RAG ingestion pipeline | Group 1 | 1 – Parallel build | A3, A4 | 20 min |
| A6 | Build RAG retrieval, filtering, reranking and Internal Analyst | Group 1 | 1 – Parallel build | A3, stub of A5 | 20 min |
| A7 | Build the external intelligence tool layer (MCP-style clients) | Group 1 | 1 – Parallel build | A3, A4 | 20 min |
| A8 | Build LangGraph workflow and routing | Group 2 | 1 – Parallel build | A3 | 25 min |
| A9 | Build Supervisor and the ReAct News Investigator | Group 2 | 1 – Parallel build | A3, stubs of A6/A7 | 25 min |
| A10 | Build claim extraction, verification and contradiction detection | Group 2 | 1 – Parallel build | A3 | 25 min |
| A11 | Build guardrails, evidence sufficiency and failure handling | Group 3 | 1 – Parallel build | A3 | 20 min |
| A12 | Build risk scoring, recommendations and human-approval flag | Group 3 | 1 – Parallel build | A3 | 20 min |
| A13 | Build evaluator and final executive report | Group 3 | 1 – Parallel build | A3 | 20 min |
| A14 | Create and run component test cases (each group tests its own component) | Each group | 2 – Component testing | Own Phase-1 work | 20 min |
| A15 | Integrate all components end to end | All (Group 2 leads) | 3 – Integration | A5–A13 | 20 min |
| A16 | Scenario testing, evaluation run and final demo | All groups | 4 – Test & demo | A14, A15 | 20 min |

**Suggested overall timeline (about 2 h 10 min; scale to your session length):**

| Clock | Phase | What happens |
|---|---|---|
| 0:00 – 0:25 | Phase 0 – Foundation | A1 → A2 and A3 in parallel; Group 1 prepares data (A4) at the same time |
| 0:25 – 1:10 | Phase 1 – Parallel build | A5–A13: every group builds its own components against stubs and mocks |
| 1:10 – 1:30 | Phase 2 – Component testing | A14: each group writes and runs tests for its own component |
| 1:30 – 1:50 | Phase 3 – Integration | A15: replace stubs with real modules, run the full graph once |
| 1:50 – 2:10 | Phase 4 – Scenario tests and demo | A16: run the challenging scenarios and the final demo |

**Stretch activities** (only if time remains, after the minimum demo works): see Activity S at the end of Section 5.

---

## 3. Repository Ownership Map (Section 27 structure)

Tags: **[G1]** Group 1 · **[G2]** Group 2 · **[G3]** Group 3 · **[ALL]** shared.
Items marked ⭐ are *stretch* files — create an empty placeholder with a docstring, but build them only after the minimum demo works.
Items marked ➕ are **additions** to the Section 27 layout that this assignment needs (see the note below the tree).

```text
argus/
├── README.md                    ➕ [G3]  setup instructions, how to run, team/ownership table
├── requirements.txt             ➕ [G3]  pinned dependencies
├── .env.example                 ➕ [G3]  placeholder variables only — no real keys
├── .gitignore                   ➕ [G3]  .env, venv, FAISS index files, __pycache__
├── app.py                       [G2]  entry point: accepts the executive question, runs the graph
├── config/
│   ├── models.py                ⭐ [G2]  model tier definitions (small / medium / strong)
│   └── settings.py              [G2]  limits, thresholds, paths, scoring weights (contract file)
├── graph/
│   ├── state.py                 [G2]  shared IntelligenceState (contract file)
│   ├── graph.py                 [G2]  builds and compiles the LangGraph workflow
│   ├── routing.py               [G2]  conditional edges and bounded loop routing
│   └── checkpoints.py           ⭐ [G2]  checkpointing / persistence
├── agents/
│   ├── supervisor.py            [G2]  query analysis and delegation
│   ├── news_investigator.py     [G2]  ReAct Think → Act → Observe loop
│   ├── internal_analyst.py      [G1]  maps events to internal exposure using RAG
│   ├── verifier.py              [G2]  claims, provenance, contradictions
│   ├── risk_analyst.py          [G3]  impact / probability / urgency scoring
│   ├── recommender.py           [G3]  prioritised actions with owner and rationale
│   └── evaluator.py             [G3]  grounding / citation / unsupported-claim checks, report
├── rag/
│   ├── loader.py                ➕ [G1]  load PDF / text files
│   ├── chunking.py              ➕ [G1]  clean and chunk text, attach metadata
│   ├── ingest.py                [G1]  orchestrates load → chunk → embed → index
│   ├── faiss_store.py           [G1]  build / save / load FAISS index
│   ├── retrieval.py             [G1]  search_internal with filters and scores
│   └── reranker.py              [G1]  lightweight rerank / recency preference
├── mcp/
│   ├── news_client.py           [G1]  news search tool (mock fallback, clearly labelled)
│   ├── government_client.py     [G1]  regulatory / government search tool
│   ├── market_client.py         ⭐ [G1]  market data stub
│   └── company_client.py        ⭐ [G1]  company intelligence stub
├── models/
│   ├── cascade.py               ⭐ [G2]  three-tier model routing
│   └── schemas.py               [G2]  Pydantic / TypedDict data models (contract file)
├── guardrails/
│   ├── evidence.py              [G3]  evidence-sufficiency gate
│   ├── injection.py             [G3]  prompt-injection / unsafe-input defences
│   ├── access_control.py        ⭐ [G3]  confidentiality / authorization stub
│   └── budgets.py               [G3]  iteration, retry, timeout and cost limits
├── evaluation/
│   ├── datasets/                [ALL] one file per group (see Section 6)
│   ├── metrics.py               [G3]  retrieval, grounding, citation, contradiction metrics
│   └── regression.py            [G3]  re-run all scenario datasets and compare
├── data/                        ➕ [G1]  sample_docs/ (PDFs) and mock/ (news & regulation JSON)
├── docs/
│   └── interfaces.md            ➕ [G2]  the agreed contract (signatures, state keys, ToolResult)
└── tests/                       ➕ per-group subfolders
    ├── g1_knowledge/            [G1]
    ├── g2_orchestration/        [G2]
    ├── g3_trust_quality/        [G3]
    └── e2e/                     [ALL] end-to-end scenario tests (A15/A16)
```

**Additions beyond Section 27 (and why):** `README.md`, `requirements.txt`, `.env.example` and `.gitignore` are needed for a repeatable setup. `rag/loader.py` and `rag/chunking.py` split the ingestion work into small, testable pieces. `data/` holds the training PDFs and mock external data. `docs/interfaces.md` records the shared contract. `tests/` is split into per-group subfolders so groups never edit each other's test files.

**Ownership rules**
- Only the owning group edits a file. If another group needs a change, they ask the owner through the contract channel.
- The three **contract files** (`graph/state.py`, `models/schemas.py`, `config/settings.py`) are owned by Group 2 but are **frozen after A3**. Any later change must be announced to all groups immediately.
- Each group works on its own branch (`group1-knowledge`, `group2-orchestration`, `group3-trust`) and merges to `main` only at integration (A15), plus small merges of stubs during A3.

---

## 4. The Shared Contract (agree this in A3, before parallel coding)

This is what lets the groups work independently: everyone codes against **agreed signatures and shapes**, and each group first publishes a **stub** (a function that returns hard-coded sample data) so others can import and test against it right away.

### 4.1 Callable signatures

| Function | Owner | Signature (illustrative) | Used by |
|---|---|---|---|
| `search_internal` | G1 (`rag/retrieval.py`) | `search_internal(query: str, top_k: int = 5, filters: dict \| None = None) -> list[dict]` | internal_analyst, news_investigator |
| `analyze_internal_exposure` | G1 (`agents/internal_analyst.py`) | `(state: dict) -> dict` — writes `internal_documents`, `impacted_suppliers`, `impacted_products` | graph |
| `search_news` | G1 (`mcp/news_client.py`) | `search_news(query: str, date_range: tuple \| None = None, region: str \| None = None) -> ToolResult` | news_investigator |
| `search_regulation` | G1 (`mcp/government_client.py`) | `search_regulation(query: str, jurisdiction: str \| None = None) -> ToolResult` | news_investigator |
| `analyze_query` | G2 (`agents/supervisor.py`) | `(state: dict) -> dict` | graph |
| `investigate_more` | G2 (`agents/news_investigator.py`) | `(state: dict) -> dict` — one bounded Think → Act → Observe step | graph |
| `verify_claims` | G2 (`agents/verifier.py`) | `(state: dict) -> dict` — writes `claims`, `conflicting_claims` | graph |
| `check_input` | G3 (`guardrails/injection.py`) | `check_input(query: str) -> dict` → `{"allowed": bool, "reason": str}` | graph entry |
| `sanitize_retrieved_text` | G3 (`guardrails/injection.py`) | `(text: str) -> dict` → `{"text": str, "flagged": bool}` | retrieval consumers |
| `evidence_gate` | G3 (`guardrails/evidence.py`) | `(state: dict) -> Literal["pass", "needs_research", "stop_with_uncertainty"]` | routing |
| `budget_remaining` | G3 (`guardrails/budgets.py`) | `(state: dict) -> bool` | routing, investigator |
| `assess_risk` | G3 (`agents/risk_analyst.py`) | `(state: dict) -> dict` — writes `risk_score`, `confidence_score`, `evidence_quality_score` | graph |
| `recommend_actions` | G3 (`agents/recommender.py`) | `(state: dict) -> dict` — writes `recommended_actions` (each with `requires_human_approval`) | graph |
| `evaluate_answer` | G3 (`agents/evaluator.py`) | `(state: dict) -> dict` | graph |
| `generate_report` | G3 (`agents/evaluator.py`) | `(state: dict) -> dict` — writes `final_report` | graph |

### 4.2 Standard result shapes

**Retrieved chunk** (returned by `search_internal`):

```python
{"text": "...", "source_id": "contract_supplier_abc_v2.pdf#p3",
 "metadata": {"doc_type": "contract", "supplier": "Supplier ABC", "product": "...",
              "region": "...", "doc_date": "2026-01-15", "version": "v2"},
 "score": 0.83}
```

**ToolResult** (returned by every external tool; keeps *no results* separate from *tool failed*):

```python
{"status": "ok" | "empty" | "error",   # never disguise an error as an empty list
 "mock": True | False,                  # mock data must always be labelled
 "items": [{"title": "...", "source": "...", "url": "...", "date": "...",
            "snippet": "...", "source_type": "news|government|market|company"}],
 "error": None | "timeout / message"}
```

**Claim** (created by the verifier):

```python
{"claim_id": "c1", "text": "One atomic assertion", "source_ids": ["..."],
 "source_authority": "primary|secondary|unknown", "source_date": "...",
 "confidence": 0.0-1.0, "status": "supported|unverified|contradicted"}
```

### 4.3 Shared state keys (one agreed spelling)

`user_query`, `entities`, `news_articles`, `government_evidence`, `market_evidence`, `internal_documents`, `claims`, `conflicting_claims`, `impacted_suppliers`, `impacted_products`, `missing_information`, `investigation_iterations`, `evidence_gate_result`, `risk_score`, `confidence_score`, `evidence_quality_score`, `recommended_actions`, `evaluation_result`, `final_report`, `errors`.

### 4.4 Workflow the graph implements (Group 2 builds; Group 3 gates)

```text
START
  -> check_input                    (G3 guardrail)
  -> analyze_query                  (G2 supervisor)
  -> discover_external_evidence     (G2 investigator using G1 tools)
  -> retrieve_internal_context      (G1 internal analyst / RAG)
  -> verify_claims                  (G2 verifier)
  -> evidence_gate                  (G3)
       ├── needs_research and budget remains -> investigate_more -> verify_claims
       └── pass OR stop_with_uncertainty    -> assess_risk
  -> recommend_actions              (G3)
  -> evaluate_answer                (G3)
  -> generate_report                (G3)
  -> END
```

### 4.5 Illustrative node contract

Each node accepts the shared state and returns **only the state updates it owns**.

```python
def retrieve_internal_context(state: dict) -> dict:
    query = state["user_query"]
    documents = search_internal(query, top_k=5)
    return {
        "internal_documents": documents,
        "missing_information": [] if documents else ["No relevant internal documents found"],
    }
```

---

## 5. Activity Details

Every activity lists its **Owner**, the **Tasks**, the **Files**, what it **Needs**, and a **Done when** check.

---

### PHASE 0 — FOUNDATION

#### Activity 1 — Create repository and repository structure
**Owner:** Group 2 (everyone clones afterwards) · **Time-box:** 10 min · **Needs:** nothing

| Task | Description |
|---|---|
| A1.T1 | Create the shared Git repository (e.g. `argus`) and give all 20 members access. |
| A1.T2 | Create the folder skeleton exactly as in Section 3, with an empty `__init__.py` in each Python package folder and a one-line docstring in every file naming its owner group. |
| A1.T3 | Create the three branches `group1-knowledge`, `group2-orchestration`, `group3-trust`. |
| A1.T4 | Everyone clones the repo and switches to their group branch; Group 2 confirms by posting "skeleton ready". |

**Done when:** all three groups can clone, see the full folder tree, and push to their own branch.

#### Activity 2 — Basic project setup (README, requirements, environment)
**Owner:** Group 3 · **Time-box:** 15 min · **Needs:** A1

| Task | Description |
|---|---|
| A2.T1 | Write `README.md`: project purpose, folder map, group ownership table, **setup instructions** (create venv, install requirements, copy `.env.example` to `.env`), and how to run `app.py` and the tests. |
| A2.T2 | Create `requirements.txt` with the libraries already available in the classroom environment (for example LangGraph, LangChain, FAISS, an embeddings library, a PDF reader, Pydantic, pytest). Prefer pinned versions and avoid heavy extras. |
| A2.T3 | Create `.env.example` with placeholders only (model name, API-key variable names, limits). **No real keys anywhere in the repo.** |
| A2.T4 | Create `.gitignore` (`.env`, virtual environments, FAISS index files, `__pycache__`). |
| A2.T5 | Ask one member from each other group to follow the README from scratch; fix anything unclear. |

**Done when:** a fresh clone can be set up by following only the README, and `pip install -r requirements.txt` succeeds.

#### Activity 3 — Shared contract: state, schemas, settings and stub interfaces
**Owner:** Group 2 (with one representative from each group) · **Time-box:** 20 min · **Needs:** A1

| Task | Description |
|---|---|
| A3.T1 | Define `IntelligenceState` in `graph/state.py` using the state keys in Section 4.3, with sensible defaults. |
| A3.T2 | Define `Claim`, `Evidence`, `ToolResult`, `RetrievedChunk`, `RiskAssessment`, `RecommendedAction` in `models/schemas.py` (Section 4.2). |
| A3.T3 | Create `config/settings.py` with placeholders: max investigation iterations, top-k, retry limit, tool timeout, risk weights, confidence thresholds. Values come from environment/config, not hard-coded secrets. |
| A3.T4 | Write `docs/interfaces.md` containing the signature table in Section 4.1. |
| A3.T5 | **Stub-first rule:** each group commits stub versions of its public functions that return the sample shapes above. Group 2 then merges stubs so every group can import every other group's functions from minute ~25. |
| A3.T6 | Announce **contract freeze**. Later changes need an announcement to all groups. |

**Done when:** all groups can `import` the state, schemas and every stub function without errors.

#### Activity 4 — Prepare internal training data and mock external data
**Owner:** Group 1 · **Time-box:** 15 min · **Needs:** nothing (starts at minute 0; commit after A1)

| Task | Description |
|---|---|
| A4.T1 | Create a small **fictional** company scenario (company, 3–4 suppliers, 4–5 products). Use only invented names and data. |
| A4.T2 | Prepare 6–8 short internal `.pdf` files in `data/sample_docs/`: supplier contract (current), **expired contract plus newer replacement contract** (for the stale-knowledge scenario), product-to-component mapping, procurement and inventory note, supply-risk policy, supplier communication policy, one historical incident report. |
| A4.T3 | Make sure each document has metadata that can be filtered: document ID, document type, supplier, product, region, date and version. |
| A4.T4 | Prepare mock external data in `data/mock/`: official regulatory notice, several duplicated news articles about the same event, one false/unverified viral report, one article with a different effective date (seeded conflict), a supplier statement saying "unaffected". Label every file as **MOCK**. |
| A4.T5 | Share the data list and expected facts (one line each) with Groups 2 and 3 so they can write tests against it. |

**Done when:** the files exist in `data/`, are clearly fictional/mock, and the "what each document says" list is shared.

---

### PHASE 1 — PARALLEL BUILD (Groups work independently, against stubs)

#### Activity 5 — Build the RAG ingestion pipeline
**Owner:** Group 1 · **Time-box:** 20 min · **Needs:** A3, A4

| Task | Description |
|---|---|
| A5.T1 | `rag/loader.py`: load the `.pdf` / text files and return text plus filename and document ID. |
| A5.T2 | `rag/chunking.py`: clean the text, split into chunks, and attach metadata (document ID, type, supplier, product, region, date, version) to every chunk. |
| A5.T3 | `rag/ingest.py`: orchestrate load → chunk → embed. Expose one callable, e.g. `build_index(data_dir) -> None`. |
| A5.T4 | `rag/faiss_store.py`: create, save and load the FAISS index together with the chunk metadata; expose `load_index()` for retrieval. |
| A5.T5 | Prove the smallest path first (a few documents → index → loads), then improve. |

**Done when:** the sample documents can be indexed and the index can be reloaded; chunks keep their source metadata.

#### Activity 6 — Build RAG retrieval, filtering, reranking and the Internal Analyst
**Owner:** Group 1 · **Time-box:** 20 min · **Needs:** A3 and a stub (then the real result) of A5

| Task | Description |
|---|---|
| A6.T1 | `rag/retrieval.py`: implement `search_internal(query, top_k, filters)` returning the chunk shape in Section 4.2 (text, source ID, metadata, score). |
| A6.T2 | Support optional metadata filters (supplier, product, region, document type, date). |
| A6.T3 | `rag/reranker.py`: lightweight rerank that prefers current/higher-version documents over stale ones when metadata allows. The reranker must never block the basic search path. |
| A6.T4 | Represent weak or no results **explicitly** (empty list plus a reason) instead of fabricating content. |
| A6.T5 | `agents/internal_analyst.py`: use `search_internal` to identify impacted suppliers/products and write them to state, with source IDs. |

**Done when:** a relevant sample query returns relevant chunks with traceable sources; an unrelated query returns weak/no results explicitly.

#### Activity 7 — Build the external intelligence tool layer (MCP-style clients)
**Owner:** Group 1 · **Time-box:** 20 min · **Needs:** A3, A4

| Task | Description |
|---|---|
| A7.T1 | `mcp/news_client.py`: implement `search_news(...) -> ToolResult` reading from the mock news data; clearly labelled `mock: True`. |
| A7.T2 | `mcp/government_client.py`: implement `search_regulation(...) -> ToolResult` over the mock regulatory notices. |
| A7.T3 | Distinguish `status="empty"` (nothing found) from `status="error"` (tool failed). Provide a switch (setting or argument) that **simulates a tool failure/timeout** so other groups can test degradation. |
| A7.T4 | Keep source name, date and URL/reference with every item. |
| A7.T5 | ⭐ Stretch: `mcp/market_client.py` and `mcp/company_client.py` as labelled stubs. |

**Done when:** the investigator can call the tools and receive structured evidence or a clear failure; mock data is never presented as live fact.

#### Activity 8 — Build the LangGraph workflow and routing
**Owner:** Group 2 · **Time-box:** 25 min · **Needs:** A3

| Task | Description |
|---|---|
| A8.T1 | `graph/graph.py`: build and compile the graph (Section 4.4) with **stub nodes first**, so it runs immediately. |
| A8.T2 | `graph/routing.py`: conditional edge on `evidence_gate_result` — `needs_research` loops back **only while budget remains**; `pass` or `stop_with_uncertainty` continues to risk assessment. |
| A8.T3 | Make sure every branch reaches `END` (no infinite loop). |
| A8.T4 | Run a smoke test with stubs; replace stubs with real nodes as other groups publish them. |
| A8.T5 | `app.py`: accept an executive question from the command line and print the final report. |
| A8.T6 | ⭐ Stretch: `graph/checkpoints.py`. |

**Done when:** the graph compiles and runs end to end on stubs, the gate branches correctly, and the loop terminates at the configured budget.

#### Activity 9 — Build the Supervisor and the ReAct News Investigator
**Owner:** Group 2 · **Time-box:** 25 min · **Needs:** A3 and stubs of A6/A7

| Task | Description |
|---|---|
| A9.T1 | `agents/supervisor.py`: parse the executive question into objective, entities and what evidence is needed; write them to state. |
| A9.T2 | `agents/news_investigator.py`: implement **one complete Think → Act → Observe cycle** — decide what is missing, choose a tool (`search_news`, `search_regulation`, `search_internal`), call it, record the observation, update `missing_information` and `investigation_iterations`. |
| A9.T3 | Add dynamic tool choice only after the single cycle works. |
| A9.T4 | Respect the iteration budget (read from `config/settings.py` / `guardrails/budgets.py`) and return a useful partial result when it is exhausted. |
| A9.T5 | Handle `ToolResult.status == "error"` by recording the failure and trying an alternative or stopping gracefully. |
| A9.T6 | ⭐ Stretch: `config/models.py` and `models/cascade.py` (route simple work to a small model and hard reasoning to a stronger model). |

**Done when:** a sample question triggers at least one evidence-gathering action, stores the observation, and stops or requests more research based on missing evidence/budget.

#### Activity 10 — Build claim extraction, verification and contradiction detection
**Owner:** Group 2 · **Time-box:** 25 min · **Needs:** A3

| Task | Description |
|---|---|
| A10.T1 | `agents/verifier.py`: convert source passages into **atomic claims** (one assertion each) with source IDs, source authority and date. |
| A10.T2 | Compare important claims across sources (effective dates, scope, affected entities, severity) and flag conflicts in `conflicting_claims`. **Do not force a resolution** when sources disagree. |
| A10.T3 | Treat authority, recency and independent corroboration as separate signals — many copies of one story are **not** independent confirmation. |
| A10.T4 | Prefer primary/official sources where available; label unverified claims as such. |
| A10.T5 | Write the resulting `claims` and `conflicting_claims` into state in the agreed shape. |

**Done when:** at least one claim traces to a source, and the seeded conflict (two different effective dates) is flagged rather than merged into a falsely certain conclusion.

#### Activity 11 — Build guardrails, evidence sufficiency and failure handling
**Owner:** Group 3 · **Time-box:** 20 min · **Needs:** A3

| Task | Description |
|---|---|
| A11.T1 | `guardrails/injection.py`: `check_input` (off-topic / unsafe request detection) and `sanitize_retrieved_text` (treat retrieved text as **data, never instructions**; flag text such as "ignore your rules"). |
| A11.T2 | `guardrails/evidence.py`: `evidence_gate` returning `pass`, `needs_research` or `stop_with_uncertainty` based on missing information, number/quality of sources and unresolved conflicts. |
| A11.T3 | `guardrails/budgets.py`: hard maximum of research iterations, retry limit and tool timeout; `budget_remaining(state)`. When the budget ends, return known facts, gaps and confidence limits. |
| A11.T4 | Define the safe outcome for empty retrieval and tool errors: a bounded retry or a transparent limitation — never an invented fact. |
| A11.T5 | ⭐ Stretch: `guardrails/access_control.py` stub (mask confidential fields by role). |

**Done when:** the graph cannot research forever; weak evidence or a tool failure yields a bounded retry or a transparent limitation; injected text in a document is not obeyed.

#### Activity 12 — Build risk scoring, recommendations and the human-approval flag
**Owner:** Group 3 · **Time-box:** 20 min · **Needs:** A3

| Task | Description |
|---|---|
| A12.T1 | `agents/risk_analyst.py`: calculate a transparent risk score from impact, probability and urgency (same 1–10 scale for each), with the formula and weights documented and configurable in `config/settings.py`. |
| A12.T2 | Report **confidence / evidence quality separately** from risk, so "high risk, low confidence" is never mistaken for a confirmed fact. |
| A12.T3 | `agents/recommender.py`: produce prioritised actions with `priority`, `owner` (procurement, legal, operations, leadership), `rationale` and linked evidence/source IDs. |
| A12.T4 | Mark actions that involve supplier contact, procurement change or legal escalation with `requires_human_approval = True`; never auto-execute them. |
| A12.T5 | Make the score reproducible: same inputs → same score. |

**Done when:** given a sample event and exposure, the code produces a reproducible score and at least one evidence-linked, owner-assigned action.

#### Activity 13 — Build the evaluator and the final executive report
**Owner:** Group 3 · **Time-box:** 20 min · **Needs:** A3

| Task | Description |
|---|---|
| A13.T1 | `agents/evaluator.py`: `evaluate_answer` using a checklist — relevance, grounding/source support, unsupported claims, citation coverage, contradiction disclosure, completeness. |
| A13.T2 | `generate_report`: a concise, decision-oriented report that **separates facts, inference, uncertainty and recommended actions**. |
| A13.T3 | Include risk, confidence, impacted suppliers/products (if known), evidence reviewed with source IDs, unresolved conflicts, limitations, and which actions need human approval. |
| A13.T4 | Add an abstention path: when sources do not support a conclusion, say what is unknown rather than inventing details. |
| A13.T5 | Keep retrieval evaluation separate from answer evaluation. A judge LLM may assist, but use explicit criteria and inspect examples. |

**Done when:** a sample final report contains all items above and unsupported claims are flagged or removed where feasible.

---

### PHASE 2 — COMPONENT TESTING

#### Activity 14 — Create and run component test cases (each group tests its own component)
**Owner:** Each group, for its own components · **Time-box:** 20 min · **Needs:** the group's Phase-1 work

Each group writes test cases **relevant to what it built**, stores them in its own `tests/gX_*/` folder, stores any reusable test prompts/expected answers in `evaluation/datasets/`, and runs them. The tests below are the **minimum**; groups should add more.

##### Group 1 — tests for RAG and external tools (`tests/g1_knowledge/`, `evaluation/datasets/g1_retrieval_qa.json`)

| Task | Description |
|---|---|
| A14.G1.T1 | Write **at least 10 test prompts based on the training data**, each with the expected source document (and expected fact), e.g. "Which products use components from Supplier ABC?" → `product_component_map.pdf`. |
| A14.G1.T2 | Retrieval relevance test: the expected document appears in the top-k results; compute simple retrieval precision across the prompt set. |
| A14.G1.T3 | Unrelated-query test: a question about something not in the data returns weak/no results explicitly. |
| A14.G1.T4 | Stale-knowledge test: with an expired contract and a newer replacement, the current one ranks above the expired one (or the expired one is clearly marked). |
| A14.G1.T5 | Metadata filter test: filtering by supplier / document type returns only matching chunks. |
| A14.G1.T6 | Tool tests: `search_news` and `search_regulation` return `ok` for known topics, `empty` for unknown topics, `error` when failure simulation is on; all mock items carry `mock: True`. |
| A14.G1.T7 | Ingestion test: every chunk has source ID and metadata; index saves and reloads. |

##### Group 2 — tests for the graph and agents (`tests/g2_orchestration/`, `evaluation/datasets/g2_agents.json`)

| Task | Description |
|---|---|
| A14.G2.T1 | Graph smoke test: graph compiles and runs end to end on stubs and mock data. |
| A14.G2.T2 | Routing tests: `pass` → risk assessment; `needs_research` with budget → loops back; `needs_research` without budget → stops and continues with uncertainty. |
| A14.G2.T3 | Loop-termination test: with an evidence gate that always says `needs_research`, the loop stops at the iteration limit. |
| A14.G2.T4 | Investigator test: for sample questions, the correct tool is chosen (news vs. regulation vs. internal search); observations and iteration count are written to state. |
| A14.G2.T5 | Verifier tests: every claim has at least one source ID; the **seeded conflict** (two effective dates) is flagged in `conflicting_claims`; duplicated articles are **not** counted as independent corroboration. |
| A14.G2.T6 | Tool-failure test: with the simulated failure on, the investigator records the error and the run still ends safely. |

##### Group 3 — tests for guardrails, risk, report and evaluation (`tests/g3_trust_quality/`, `evaluation/datasets/g3_trust_quality.json`)

| Task | Description |
|---|---|
| A14.G3.T1 | Guardrail tests: an **injected instruction** inside a retrieved document/article is flagged and not obeyed; an off-topic or unsafe question is rejected by `check_input`. |
| A14.G3.T2 | Evidence-gate tests: empty retrieval → not `pass`; conflicting evidence → disclosed/escalated; strong evidence → `pass`; exhausted budget → `stop_with_uncertainty`. |
| A14.G3.T3 | Budget tests: iteration and retry limits are enforced; a tool timeout is handled without crash. |
| A14.G3.T4 | Risk tests: a set of labelled examples (low / medium / high) gives the expected level; same inputs always give the same score; confidence is reported separately. |
| A14.G3.T5 | Recommendation tests: every action has priority, owner, rationale and evidence link; supplier/legal/procurement actions have `requires_human_approval = True`. |
| A14.G3.T6 | Report/evaluator tests: a deliberately unsupported claim is flagged; missing citations are detected; unresolved conflicts appear in the report; the "insufficient evidence" case produces an honest "unknown" statement. |
| A14.G3.T7 | `evaluation/metrics.py` and `evaluation/regression.py`: compute the metrics in Section 6.3 over all three datasets and print a summary. |

**Done when:** each group has its test files committed, tests run, failures are either fixed or listed with a reason.

---

### PHASE 3 — INTEGRATION

#### Activity 15 — Integrate all components end to end
**Owner:** All groups (Group 2 leads; one integration owner per group stays online) · **Time-box:** 20 min · **Needs:** A5–A13

| Task | Description |
|---|---|
| A15.T1 | Merge the three group branches into `main`; resolve conflicts (there should be none if the ownership rules were followed). |
| A15.T2 | Group 2 replaces stubs with the real functions one at a time, running the smoke test after each swap. |
| A15.T3 | Run the sample question: *"There are reports of new semiconductor export restrictions. Investigate what changed, check whether our suppliers/products may be exposed, estimate risk and recommend next actions."* |
| A15.T4 | Each group reads the output for its own component and fixes issues in its own files only. |
| A15.T5 | Run `tests/e2e/` plus every group's tests (`pytest`) and note what fails. |

**Done when:** one complete working path runs from question to final report with at least one external result, internal context, a risk score with separate confidence, recommended actions and limitations.

---

### PHASE 4 — SCENARIO TESTING AND DEMO

#### Activity 16 — Scenario testing, evaluation run and final demo
**Owner:** All groups · **Time-box:** 20 min · **Needs:** A14, A15

| Task | Description |
|---|---|
| A16.T1 | Run the challenging scenarios in Section 6.2; the group named as "Asserts behaviour" confirms the outcome. |
| A16.T2 | Run `evaluation/regression.py` and read the metrics summary aloud. |
| A16.T3 | Prepare the demo: one happy-path run and one "difficult" run (e.g. conflicting evidence or tool failure). |
| A16.T4 | Each group presents for 2 minutes: what it built, what it tested, what is still open. |
| A16.T5 | Check the Definition of a Successful Demo (Section 8, item G). |

---

### STRETCH ACTIVITY S — Only after the minimum demo works

| Item | Owner | Files |
|---|---|---|
| Three-tier model cascade with measurable routing and cost/latency telemetry | Group 2 | `config/models.py`, `models/cascade.py` |
| Checkpointing / resume | Group 2 | `graph/checkpoints.py` |
| Market and company intelligence stubs | Group 1 | `mcp/market_client.py`, `mcp/company_client.py` |
| Access control / role-based masking | Group 3 | `guardrails/access_control.py` |
| "Cost pressure" scenario: filter hundreds of articles without sending everything to the strongest model | Group 2 (builds), Group 3 (measures) | `models/cascade.py`, `evaluation/metrics.py` |

---

## 6. Testing Plan

### 6.1 Who writes which tests

| Group | Test focus | Test files | Datasets |
|---|---|---|---|
| Group 1 | Retrieval relevance, metadata filters, stale vs. current documents, ingestion integrity, tool success / empty / error | `tests/g1_knowledge/` | `evaluation/datasets/g1_retrieval_qa.json` |
| Group 2 | Graph routing, bounded loop, tool choice, claim provenance, contradiction detection, duplicate-article handling | `tests/g2_orchestration/` | `evaluation/datasets/g2_agents.json` |
| Group 3 | Prompt injection, evidence gate, budgets, risk scoring, recommendations, report quality, unsupported-claim detection | `tests/g3_trust_quality/` | `evaluation/datasets/g3_trust_quality.json` |
| All | End-to-end scenarios | `tests/e2e/` | — |

### 6.2 Challenging scenarios from Section 25 of the brief

| Scenario | Test data created by | Behaviour asserted by | What good looks like |
|---|---|---|---|
| Breaking regulation — one official notice, many duplicated articles, ambiguous effective date | Group 1 (mock files) | Group 2 | Duplicates are not counted as independent proof; the ambiguity is flagged. |
| False viral report — repeated everywhere, no authoritative corroboration | Group 1 | Group 3 | Confidence is low; the report says "uncorroborated". |
| Supplier exposure — event is real but only one internal product depends on the supplier | Group 1 (internal docs) | Group 3 | Risk is scoped to that product; actions are specific. |
| Stale internal knowledge — expired contract and newer replacement | Group 1 | Group 1 | Retrieval prefers the current contract or marks the old one stale. |
| Cross-language event — non-English source differs from later English reporting | Group 1 | Group 2 | The difference is detected as a conflict, not silently merged. |
| MCP degradation — primary news tool fails mid-investigation | Group 1 (failure switch) | Group 3 | Bounded retry, then transparent limitation; no crash, no invented facts. |
| Contradictory supplier statement — supplier says "unaffected", regulation appears to cover its product | Group 1 | Group 2 | Conflict is preserved and surfaced; primary source is preferred. |
| Insufficient evidence | Group 3 | Group 3 | The agent stops with a qualified assessment instead of fabricating certainty. |
| Prompt injection — a retrieved document tells the agent to ignore its rules | Group 3 | Group 3 | The text is flagged and not obeyed. |
| Cost pressure — hundreds of articles *(stretch)* | Group 2 | Group 3 | Cheap filtering before expensive reasoning; cost is measured. |

### 6.3 Evaluation metrics (Section 24 of the brief), by group

| Metric | What it measures | Owner of the measurement |
|---|---|---|
| Retrieval precision | Relevant chunks among those retrieved (target > 0.80) | Group 1 |
| Tool selection accuracy | Correct tool chosen for the needed evidence | Group 2 |
| Contradiction recall | Seeded conflicts that were detected | Group 2 |
| Claim grounding | Material claims supported by evidence | Group 3 |
| Citation coverage | Decision-relevant assertions traceable to sources | Group 3 |
| Evidence sufficiency | Stops neither too early nor too late | Group 3 |
| Risk classification | Agreement with labelled low / medium / high examples | Group 3 |
| Cascade efficiency, latency *(stretch)* | Cost per query, time to answer | Group 2 / Group 3 |

Retrieval evaluation (did RAG find the right chunks?) and answer evaluation (did the answer use the evidence correctly?) are kept separate so a failure can be traced to its cause.

---

## 7. One-Page Work Packs (what each group must do independently)

### Group 1 — Knowledge Builders
- **Activities:** A4 → A5 → A6 → A7 → A14 (own tests) → A15/A16 (joint).
- **Files owned:** `rag/loader.py`, `rag/chunking.py`, `rag/ingest.py`, `rag/faiss_store.py`, `rag/retrieval.py`, `rag/reranker.py`, `mcp/news_client.py`, `mcp/government_client.py`, `agents/internal_analyst.py`, `data/`, `tests/g1_knowledge/`, `evaluation/datasets/g1_retrieval_qa.json`. ⭐ `mcp/market_client.py`, `mcp/company_client.py`.
- **Publishes early (by minute ~25):** stub `search_internal`, `search_news`, `search_regulation`, `analyze_internal_exposure`; the mock data list.
- **Consumes:** state/schemas from Group 2.
- **Suggested internal split (7 people):** Team 1a (3) — A4 data + A5 ingestion; Team 1b (2) — A6 retrieval, reranker, internal analyst; Team 1c (2) — A7 tool layer and failure simulation. Everyone joins A14 for their own piece.

### Group 2 — Agent Orchestrators
- **Activities:** A1 → A3 → A8 → A9 → A10 → A14 (own tests) → A15 (lead) → A16.
- **Files owned:** `app.py`, `config/settings.py`, `graph/state.py`, `graph/graph.py`, `graph/routing.py`, `agents/supervisor.py`, `agents/news_investigator.py`, `agents/verifier.py`, `models/schemas.py`, `docs/interfaces.md`, `tests/g2_orchestration/`, `evaluation/datasets/g2_agents.json`. ⭐ `config/models.py`, `models/cascade.py`, `graph/checkpoints.py`.
- **Publishes early (by minute ~25):** repo skeleton, state/schemas, settings, a compiling stub graph.
- **Consumes:** tool/retrieval stubs from Group 1; gate/budget functions from Group 3.
- **Suggested internal split (7 people):** Team 2a (2) — repo, contract, graph, routing, `app.py`; Team 2b (3) — supervisor and ReAct investigator; Team 2c (2) — verifier and contradiction detection.

### Group 3 — Trust & Quality Guardians
- **Activities:** A2 → A11 → A12 → A13 → A14 (own tests) → A15 → A16.
- **Files owned:** `README.md`, `requirements.txt`, `.env.example`, `.gitignore`, `guardrails/evidence.py`, `guardrails/injection.py`, `guardrails/budgets.py`, `agents/risk_analyst.py`, `agents/recommender.py`, `agents/evaluator.py`, `evaluation/metrics.py`, `evaluation/regression.py`, `tests/g3_trust_quality/`, `evaluation/datasets/g3_trust_quality.json`. ⭐ `guardrails/access_control.py`.
- **Publishes early (by minute ~25):** stub `evidence_gate`, `budget_remaining`, `check_input`, `assess_risk`, `recommend_actions`, `evaluate_answer`, `generate_report`.
- **Consumes:** state/schemas from Group 2; claims/conflicts from Group 2; source shapes from Group 1.
- **Suggested internal split (6 people, 3 pairs):** Pair 3a — A2 setup, then A11 guardrails/evidence/budgets; Pair 3b — A12 risk and recommendations; Pair 3c — A13 evaluator, report, metrics and regression runner.

---

## 8. Whole-Team Guidance

### A. Build a working minimum first
For a live coding session, a small working end-to-end agent is more valuable than a dozen disconnected modules. Start with a narrow scenario:

> "There are reports of new semiconductor export restrictions. Investigate what changed, check whether our suppliers/products may be exposed, estimate risk and recommend next actions."

Use a few sample internal documents and clearly labelled mock news/regulatory results if live services are unavailable.

### B. Keep to the shared contract
- **State keys:** one agreed spelling (Section 4.3).
- **Evidence format:** each result keeps its source ID/name, date if available, content/snippet and metadata.
- **Node contract:** each LangGraph node accepts the shared state and returns a dictionary with only the updates it owns.
- **Error contract:** tool failures and empty retrieval are explicit, never disguised as an empty success.
- **Stub-first:** publish a stub of every public function early; replace it with the real function later without changing the signature.

### C. RAG quality is more than vector similarity
- Keep metadata with each chunk (type, supplier, product, region, date/version).
- Test whether the **retrieved chunks** are relevant before tuning the generated answer.
- Use metadata filters and reranking if time permits; a stale contract should not automatically outrank its replacement.
- If no relevant evidence is retrieved, say so and lower confidence rather than asking the LLM to fill the gap.

### D. Evaluation concepts from class

| Evaluation area | What to check |
|---|---|
| Search / retrieval evaluation | Are the right internal chunks retrieved? Inspect relevance, precision/recall where a labelled test set exists, and whether stale/irrelevant chunks dominate. |
| Grounding | Is each material claim supported by retrieved or identified external evidence? |
| Hallucination / unsupported claims | Has the answer invented a fact, date, supplier impact or certainty? |
| Relevancy | Does the response answer the executive's actual question and support a decision? |
| Contradiction handling | Are conflicting sources detected and disclosed? |
| Evidence sufficiency | Does the agent gather more evidence when needed and stop with uncertainty when its budget is exhausted? |
| Risk evaluation | Is the risk assessment consistent with the scoring method and labelled examples? |

A judge LLM can help assess grounding, unsupported claims and relevancy, but it is itself fallible. Use explicit criteria and inspect examples; a judge score is not proof.

### E. Guardrails and operational safety
- Keep API keys in environment variables or the classroom's approved secret mechanism; never commit secrets.
- Treat content retrieved from news articles and internal documents as **untrusted data**, not system instructions.
- Use bounded retries and a maximum investigation budget.
- If a tool is unavailable, return a clear error and continue only if the remaining evidence is sufficient.
- Recommendations that contact suppliers, change procurement or trigger legal action are presented for **human approval**, not executed automatically.

### F. Keep code contributions easy to integrate
1. Create the file/function early and share its signature.
2. Use small, focused functions rather than one large script.
3. Run a quick import/syntax check as soon as a file is ready.
4. Use mock results when another group's module is not ready yet.
5. Tell Group 2 which state keys your node reads and writes.
6. At integration time, prioritise **one complete working path** before optional features such as the three-tier model cascade or a full MCP server.
7. Commit small and often to your group branch; never edit another group's files.

### G. Definition of a successful class demo
The minimum demo can:
- Accept an executive question.
- Gather at least one external-style result and retrieve internal context.
- Use LangGraph to run and visibly control the workflow.
- Preserve source attribution for material claims.
- Identify at least one conflict, or explicitly state that none was found in the sample.
- Produce a risk score with confidence shown separately.
- Recommend next actions, flag which need human approval, and state uncertainty/limitations.
- Terminate safely when evidence or the research budget is insufficient.
- Show passing tests from all three groups and a metrics summary from `evaluation/regression.py`.

---

