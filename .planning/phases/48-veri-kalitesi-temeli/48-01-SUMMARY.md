---
phase: 48-veri-kalitesi-temeli
plan: "01"
subsystem: backend
tags: [data-quality, scoring, migration, api]
dependency_graph:
  requires: []
  provides: [data_quality_score-column, calculate_data_quality_score-function, stocks-api-data-quality]
  affects: [scoring-engine, stocks-api]
tech_stack:
  added: []
  patterns: [idempotent-alembic-inspector, tdd-red-green, singleton-service]
key_files:
  created:
    - backend/alembic/versions/008_add_data_quality_score.py
    - backend/tests/test_data_quality_score.py
  modified:
    - backend/app/models/stock.py
    - backend/app/services/scoring.py
    - backend/app/api/stocks.py
decisions:
  - "Use net_income (actual Fundamental model field) instead of net_profit (plan pseudocode) for null-penalty check"
  - "Replace _list_data_quality_score computed helper with DB column s.data_quality_score in list endpoint"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-15"
  tasks_completed: 3
  files_changed: 5
---

# Phase 48 Plan 01: Data Quality Score Foundation Summary

**One-liner:** Idempotent migration 008 adds `data_quality_score FLOAT` to stocks, with a `calculate_data_quality_score(fundamental)` scorer (100 base, -30 per USD-suspicious ratio, -10 per null field, clamped 0-100) wired into `update_all_scores()` and both `/stocks` and `/stocks/{symbol}` API responses.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Alembic migration 008 + Stock ORM column | 91f8eb1 | 008_add_data_quality_score.py, stock.py |
| 2 (RED) | Failing tests for calculate_data_quality_score | b1d3271 | tests/test_data_quality_score.py |
| 2 (GREEN) | Implement function + update_all_scores integration | 4fb2fb6 | scoring.py |
| 3 | Expose data_quality_score in API endpoints | 85768b9 | stocks.py |

## Verification Results

- `revision = "008"` — PASS
- `down_revision = "007"` — PASS
- `data_quality_score = Column(Float, nullable=True)` in stock.py — PASS
- `def calculate_data_quality_score` top-level in scoring.py — PASS
- `stock.data_quality_score = calculate_data_quality_score(fundamental)` in update_all_scores — PASS
- `pytest tests/test_data_quality_score.py` — 7/7 PASSED
- `grep -c '"data_quality_score":' backend/app/api/stocks.py` returns 2 — PASS
- `from app.services.scoring import scoring_engine` — import OK
- `from app.api.stocks import router` — import OK
- Alembic `upgrade head` ran successfully (007 → 008 applied to DB)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used `net_income` instead of `net_profit` for null-penalty field**
- **Found during:** Task 2 (RED phase, while writing tests)
- **Issue:** Plan pseudocode used `getattr(fundamental, "net_profit", None)` but `Fundamental` ORM model defines the column as `net_income` (see `backend/app/models/fundamental.py` line 48). Using `net_profit` would always return `None` (via getattr default), silently applying a false null penalty to every stock.
- **Fix:** Used `net_income` as the field name in both the function implementation and the test fixtures.
- **Files modified:** backend/app/services/scoring.py, backend/tests/test_data_quality_score.py
- **Commit:** 4fb2fb6

**2. [Rule 1 - Bug] Replaced computed helper with DB column in list endpoint**
- **Found during:** Task 3 (reading stocks.py)
- **Issue:** `GET /stocks` already had `"data_quality_score": _list_data_quality_score(s)` — a computed proxy score based on index membership and score availability, not the fundamental-based VKL formula. Leaving both would shadow the DB column.
- **Fix:** Replaced `_list_data_quality_score(s)` with `s.data_quality_score` (the DB column) in the list serialization dict. The `_list_data_quality_score` helper function remains in the file as it may be used elsewhere (score-breakdown guardrail component), but is no longer called from the list endpoint.
- **Files modified:** backend/app/api/stocks.py
- **Commit:** 85768b9

## Known Stubs

None — `data_quality_score` is computed deterministically from real Fundamental data. Until `update_all_scores()` runs, values will be `null` in the DB (expected behavior documented in VKL-02 acceptance criteria). No placeholder text or hardcoded empty values.

## Self-Check: PASSED

- `backend/alembic/versions/008_add_data_quality_score.py` — FOUND
- `backend/tests/test_data_quality_score.py` — FOUND
- Commits 91f8eb1, b1d3271, 4fb2fb6, 85768b9 — all verified in git log
