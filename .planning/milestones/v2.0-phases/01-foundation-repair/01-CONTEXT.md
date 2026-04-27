# Phase 1: Foundation Repair - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 5 silent data-corruption defects in the backend so the rest of the system can be trusted. No new features, no UI changes. The goal is: every data pipeline produces only real data, config values actually affect runtime behavior, unused 3-4GB dependencies are gone, endpoints are organized into domain routers, and all timestamps in the database are UTC-aware.

Requirements in scope: FOND-01, FOND-02, FOND-03, FOND-04, FOND-05.

</domain>

<decisions>
## Implementation Decisions

### KAP Failure Mode (FOND-01)

- **D-01:** If `feedparser` is not installed, the backend fails at startup with a clear `RuntimeError` — feedparser is treated as a required dependency, not optional
- **D-02:** If feedparser IS installed but KAP RSS is temporarily unreachable (network error, malformed feed, timeout) → return an empty list + write a `WARNING` log. The scheduler continues running and will retry on the next interval.
- **D-03:** `_generate_mock_announcements()` is completely deleted — no mock path should be reachable from production code. All three fallback paths (lines 66-68, 103, 110 in kap_parser.py) are removed.

### Scoring Weights (FOND-02)

- **D-04:** `config.py` values win. The authoritative weights are:
  - `WEIGHT_TECHNICAL = 0.20`
  - `WEIGHT_FUNDAMENTAL = 0.25`
  - `WEIGHT_ML = 0.20`
  - `WEIGHT_SENTIMENT = 0.10`
  - `WEIGHT_CAUSAL = 0.15`
  - `WEIGHT_MACRO = 0.10`
- **D-05:** `WEIGHT_MACRO` maps to `Stock.macro_score` column — if the column exists and has a value, include it in the weighted sum; if null/missing, treat as 0 (neutral contribution)
- **D-06:** `scoring.py` `BASE_WEIGHTS` class constant is removed entirely. `ScoringEngine` reads all weights from `settings` (the pydantic-settings singleton) at runtime. Changing a weight in config.py (or .env) is immediately reflected — zero code changes elsewhere required.

### Router Structure (FOND-04)

- **D-07:** Domain-based file split into 6 router files inside `backend/app/api/`:
  - `stocks.py` — stock list, stock detail, rankings, scoring endpoints
  - `macro.py` — TCMB, TUIK, macro indicators, FX/commodity data
  - `portfolio.py` — user portfolio and model portfolio endpoints
  - `intelligence.py` — market intelligence, event fusion, correlation
  - `causal.py` — causal chain analysis endpoints
  - `admin.py` — health check, manual scan triggers
- **D-08:** `endpoints.py` is deleted entirely after all content is moved to domain routers
- **D-09:** `main.py` uses one `app.include_router(x.router, prefix="/api")` call per domain router — no aggregator __init__.py

### Unused Dependencies (FOND-03)

- **D-10:** Remove from `requirements.txt`: `tensorflow`, `torch`, `transformers`, `sentencepiece` — all confirmed unused in codebase (STACK.md audit)
- **D-11:** Verify `vaderSentiment` usage before removing — it appears in `macro_news.py`; keep if used

### UTC Timestamps (FOND-05)

- **D-12:** `model_portfolio.py` is the primary offender — `DateTime` → `DateTime(timezone=True)` and `datetime.utcnow` → `func.now()`. Fix inline using SQLAlchemy's existing pattern (matching all other models).
- **D-13:** Scan all service layer files for `datetime.utcnow()` or `datetime.now()` used in DB writes and replace with `datetime.now(timezone.utc)` from Python's `datetime` module.
- **D-14:** No Alembic migration needed for this phase — the existing `Base.metadata.create_all()` lifespan hook handles table updates on restart.

### Claude's Discretion

- How to organize the health check endpoint (in admin.py or keep as a standalone route)
- Whether `macro_news.py` endpoints go in `macro.py` or `intelligence.py`
- Exact log message wording for KAP WARNING events

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### KAP Parser
- `backend/app/services/kap_parser.py` — All 3 mock fallback paths (lines 66-68, 103, 110) and `_generate_mock_announcements()` to be removed
- `backend/app/main.py` — lifespan function where startup validation should be added

### Scoring Engine
- `backend/app/services/scoring.py` — `BASE_WEIGHTS` class constant (lines 22-28) to be replaced with settings reads
- `backend/app/core/config.py` — `WEIGHT_*` settings (lines 53-58) are the authoritative values
- `backend/app/models/stock.py` — check if `macro_score` column exists

### Router Split
- `backend/app/api/endpoints.py` — all 31 endpoints to be migrated (check each endpoint's domain ownership)
- `backend/app/main.py` — `include_router` call (line 159) to be replaced with 6 domain calls

### Timestamp Fix
- `backend/app/models/model_portfolio.py` — `DateTime` without timezone (lines 14-15), primary target
- `backend/app/models/` — all other model files (other models already use `timezone=True`, use as reference pattern)

### Dependency Cleanup
- `backend/requirements.txt` — authoritative dependency list
- `backend/app/services/macro_news.py` — verify `vaderSentiment` usage before removing

No external specs — requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `backend/app/core/config.py` `Settings` class — all WEIGHT_* values already defined here; just needs scoring.py to read them
- `backend/app/models/stock.py` — `timezone=True` pattern is established and working; copy for model_portfolio.py fix
- `backend/app/main.py` lifespan — correct place for feedparser startup check (alongside existing `init_db()` call)

### Established Patterns

- All existing models except model_portfolio.py already use `DateTime(timezone=True)` + `func.now()` — the correct pattern is established
- FastAPI router pattern: `router = APIRouter()` with `@router.get(...)` decorators — use same pattern in new domain files
- `logger = logging.getLogger(__name__)` — per-module logger pattern, use in all new router files

### Integration Points

- `backend/app/main.py` — single mount point for all routers; changing `include_router` calls here
- `backend/app/services/scoring.py` `ScoringEngine._resolve_weights()` — where BASE_WEIGHTS are read; this method needs to pull from `settings` instead
- `backend/app/services/kap_parser.py` `scan_announcements()` — the method whose 3 fallback paths must be cleaned

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants the mock code gone entirely — not just unreachable but deleted
- Config.py is the single source of truth for scoring weights going forward — no duplication in service layer

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation-repair*
*Context gathered: 2026-04-16*
