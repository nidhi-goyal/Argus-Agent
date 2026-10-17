# ARGUS shared interfaces

These signatures and state names implement Assignment Sections 4.1–4.5. Nodes
accept the shared state dictionary and return only the fields they update.

## Public call signatures

| Function | Owner | Signature | Purpose |
|---|---|---|---|
| `search_internal` | G1 | `search_internal(query: str, top_k: int = 5, filters: dict \| None = None) -> list[dict]` | Search internal chunks; an empty `SearchResults` has a `reason` attribute. |
| `analyze_internal_exposure` | G1 | `analyze_internal_exposure(state: dict) -> dict` | Write internal documents, impacted suppliers/products, and internal gaps. |
| `search_news` | G1 | `search_news(query: str, date_range: tuple \| None = None, region: str \| None = None) -> ToolResult` | Search mock news; accepts `simulate_failure=True` for tests. |
| `search_regulation` | G1 | `search_regulation(query: str, jurisdiction: str \| None = None) -> ToolResult` | Search mock official notices; accepts `simulate_failure=True` for tests. |
| `analyze_query` | G2 | `analyze_query(state: dict) -> dict` | Set objective, entities, evidence needs, and initial gaps. |
| `investigate_more` | G2 | `investigate_more(state: dict) -> dict` | Perform one bounded Think → Act → Observe step. |
| `verify_claims` | G2 | `verify_claims(state: dict) -> dict` | Add source-linked claims, confidence, and unresolved conflicts. |
| `check_input` | G3 | `check_input(query: str) -> dict` | Return `{"allowed": bool, "reason": str}`. |
| `sanitize_retrieved_text` | G3 | `sanitize_retrieved_text(text: str) -> dict` | Return `{"text": str, "flagged": bool}`; preserve evidence but flag instructions. |
| `evidence_gate` | G3 | `evidence_gate(state: dict) -> Literal["pass", "needs_research", "stop_with_uncertainty"]` | Decide whether evidence is sufficient or budget is exhausted. |
| `budget_remaining` | G3 | `budget_remaining(state: dict) -> bool` | Prevent unbounded research. |
| `assess_risk` | G3 | `assess_risk(state: dict) -> dict` | Write score, risk level, confidence, evidence quality, and formula. |
| `recommend_actions` | G3 | `recommend_actions(state: dict) -> dict` | Write prioritized, evidence-linked actions with approval flags. |
| `evaluate_answer` | G3 | `evaluate_answer(state: dict) -> dict` | Return explicit grounding, citation, contradiction, and completeness checks. |
| `generate_report` | G3 | `generate_report(state: dict) -> dict` | Write a decision-oriented report separating fact, inference, and uncertainty. |

## State keys

`IntelligenceState` in `graph/state.py` is the shared graph contract. Its core
keys are `user_query`, `entities`, `news_articles`, `government_evidence`,
`market_evidence`, `internal_documents`, `claims`, `conflicting_claims`,
`impacted_suppliers`, `impacted_products`, `missing_information`,
`investigation_iterations`, `evidence_gate_result`, `risk_score`,
`confidence_score`, `evidence_quality_score`, `recommended_actions`,
`evaluation_result`, `final_report`, and `errors`. Additional audit fields
include `tool_calls`, `observations`, `source_ids`, `injection_flags`, and
`evidence_limitations`.

Use `graph.state.new_state(user_query)` to get a fresh state with empty lists and
safe defaults. Per-run arrays are not shared.

## Standard result shapes

**Retrieved chunk**

```python
{
    "text": "...",
    "source_id": "contract_supplier_v2.pdf#chunk1",
    "metadata": {
        "doc_type": "contract", "supplier": "Fictional Supplier",
        "product": "Fictional Product", "region": "North America",
        "doc_date": "2026-01-15", "version": "v2"
    },
    "score": 0.83
}
```

**ToolResult** — `empty` means the search succeeded but found nothing;
`error` means the tool failed. Mock sources always identify themselves.

```python
{
    "status": "ok" | "empty" | "error",
    "mock": True | False,
    "items": [{
        "title": "...", "source": "...", "url": "...", "date": "...",
        "snippet": "...", "source_type": "news|government|market|company",
        "source_id": "..."
    }],
    "error": None | "timeout / message"
}
```

**Claim**

```python
{
    "claim_id": "c1", "text": "One factual assertion",
    "claim_type": "effective_date", "source_ids": ["source-1"],
    "source_authority": "primary|secondary|unknown", "source_date": "2026-08-10",
    "confidence": 0.0, "status": "supported|unverified|contradicted",
    "independent_source_count": 1
}
```

`duplicate_of` groups syndicated copies to avoid counting them as independent
corroboration. Conflicting claims remain in state with status `unresolved`;
ARGUS does not silently select one side.

## Workflow and routing

```text
START -> check_input -> analyze_query -> discover_external_evidence
      -> retrieve_internal_context -> verify_claims -> evidence_gate
           needs_research + budget -> investigate_more -> verify_claims
           pass or exhausted budget -> assess_risk -> recommend_actions
      -> evaluate_answer -> generate_report -> END
```

Rejected inputs follow a safe path directly to `END`. Each loop iteration is
counted and capped by `ARGUS_MAX_ITERATIONS`. The risk formula is a weighted
average of impact, probability, and urgency (each 1–10); its weights are
environment-configurable and must sum to 1. Confidence and evidence quality are
reported separately from risk.

