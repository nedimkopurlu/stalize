# Phase 6: Teknik Düzeltmeler - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Pure backend refactoring phase — close four audit findings with no user-facing behavior changes:
1. APScheduler job overlap protection (max_instances=1, misfire_grace_time=300)
2. Sync yfinance calls → async via run_in_executor (data_collector.py, macro.py)
3. Deprecated fillna(method="ffill") → ffill() in dynamic_correlation.py
4. ML double-count fix: remove causal_score*0.2 from ml.py _normalize_score()

No new endpoints, no UI changes, no new dependencies.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices are at Claude's discretion — pure infrastructure phase.

- APScheduler: add max_instances=1 and misfire_grace_time=300 to every scheduler.add_job() call in main.py
- async yfinance: wrap with asyncio.get_event_loop().run_in_executor(None, sync_fn) — no new thread pool needed
- fillna: replace fillna(method="ffill") with ffill() — pandas positional API
- ML double-count: in ml.py _normalize_score(), remove the causal_score * 0.2 blend; causal enters only through scoring.py weights

</decisions>

<code_context>
## Existing Code Insights

### Key Files to Modify
- `backend/app/main.py` — all scheduler.add_job() calls need max_instances and misfire_grace_time
- `backend/app/services/data_collector.py` — get_ticker_history(), get_ticker_info() are sync
- `backend/app/api/macro.py` — yf.download() call is sync inside async handler
- `backend/app/services/dynamic_correlation.py` — fillna(method="ffill") on line ~124
- `backend/app/services/ml.py` — _normalize_score() blends causal_score * 0.2

### Established Patterns
- Tests in backend/tests/ use pytest + asyncio
- Existing run_in_executor usage: check if any precedent exists in codebase
- APScheduler jobs: AsyncIOScheduler in main.py

### Integration Points
- scoring.py already has causal_score at weight 0.15 — after fix, this is the ONLY place causal enters
- overall_score formula must still sum to 1.0 across all weights after ML fix

</code_context>

<specifics>
## Specific Ideas

- For each APScheduler job, add kwargs: max_instances=1, misfire_grace_time=300
- run_in_executor pattern: `await asyncio.get_event_loop().run_in_executor(None, lambda: yf.download(...))`
- After ML fix, add a test asserting causal is not in ml.py _normalize_score internals

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-teknik-duzeltmeler*
*Context gathered: 2026-04-19*
