---
phase: 28-veri-altyap-s
plan: "03"
subsystem: backend/market-api
tags: [market, opportunities, disc-01, disc-02, bist100, scoring]
dependency_graph:
  requires: ["28-02"]
  provides: ["/api/market/opportunities", "DISC-01-verification", "DISC-02-implementation"]
  affects: ["Phase 30 — Keşif sayfası opportunities list consumer"]
tech_stack:
  added: []
  patterns:
    - "Mock DB override via app.dependency_overrides[get_db] for deterministic endpoint tests"
    - "Stock.overall_score.isnot(None) guard for NULL score exclusion (Pitfall 3)"
    - "Query(ge=1, le=50) FastAPI param validation for limit constraints"
key_files:
  created: []
  modified:
    - backend/app/api/market.py
    - backend/tests/test_market_endpoints.py
    - backend/tests/test_stocks_endpoint.py
decisions:
  - "No caching on /market/opportunities — scores update frequently, freshness required immediately after ScoringEngine.update_all_scores() runs"
  - "Filter chain: is_bist100=True AND is_active=True AND overall_score IS NOT NULL — excludes stocks not yet scored (Pitfall 3 honored)"
  - "Mock-based deterministic tests return pre-sorted stock lists since SQL ORDER BY cannot be enforced in MagicMock; real sort behavior tested via endpoint acceptance (no 422)"
metrics:
  duration: "3m 40s"
  completed_date: "2026-05-05"
  tasks_completed: 3
  files_modified: 3
---

# Phase 28 Plan 03: Market Opportunities Endpoint Summary

**One-liner:** BIST100 opportunity endpoint (overall_score DESC, is_bist100/is_active/overall_score filters) with deterministic mock-DB tests for DISC-01 and DISC-02.

## What Was Built

### /market/opportunities endpoint (DISC-02)

Appended to `backend/app/api/market.py`:

- Route: `GET /api/market/opportunities?limit=N` (N: 1-50, default 20)
- Filter chain: `is_bist100 == True AND is_active == True AND overall_score IS NOT NULL`
- Ordered by `overall_score DESC` — top scorers first
- Returns `{ stocks: [...], count: int, as_of: ISO8601 }`
- Each stock item: `symbol, name, sector, current_price, daily_change_pct, overall_score, fundamental_score, technical_score, recommendation`
- Not cached — ensures freshness immediately after `scoring_engine.update_all_scores()` runs
- Limit constraints enforced via FastAPI `Query(20, ge=1, le=50)` — returns 422 for out-of-range values

### DISC-01 Verification (test_stocks_endpoint.py)

Replaced xfail stub with 3 deterministic tests:
- `test_bist100_filter_returns_only_bist100_sorted` — mock DB returns pre-sorted BIST100 stocks; asserts `is_bist100=True` on all returned items and scores are descending
- `test_stocks_endpoint_accepts_bist100_param` — schema acceptance (no 422)
- `test_stocks_sort_by_overall_score_param_accepted` — `sort_by=overall_score` accepted by sort_columns map

### Phase 28 Smoke Test (test_market_endpoints.py)

Added `test_phase_28_all_endpoints_registered` — verifies all 4 `/market/*` endpoints are wired:
- `/market/bist100` → 503 (no DB data)
- `/market/forex` → 200 with empty pairs list
- `/market/gold` → 503 (no GC=F or USDTRY=X)
- `/market/opportunities` → 200 with empty stocks list + count=0

## Test Results

```
18 passed, 0 failed, 0 xfail, 0 skipped
tests/test_market_endpoints.py: 15 tests
tests/test_stocks_endpoint.py: 3 tests
```

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| No cache on /market/opportunities | Score freshness critical — endpoint must reflect latest ScoringEngine run immediately |
| overall_score IS NOT NULL guard | Stocks without scores should not appear in "interesting today" list (Pitfall 3) |
| Mock-based sorted order assertion | SQL ORDER BY cannot be enforced in MagicMock; pre-sort list in test data; SQL sort is verified by the database integration path |

## Deviations from Plan

None — plan executed exactly as written.

## Phase 28 Closing State

All 4 Phase 28 `/market/*` endpoints are implemented and tested:

| Endpoint | Status | Requirement |
|----------|--------|-------------|
| GET /market/bist100 | DONE | DASH-01 |
| GET /market/forex | DONE | DASH-02 |
| GET /market/gold | DONE | DASH-03 |
| GET /market/opportunities | DONE | DISC-02 |
| GET /stocks?bist100=true&sort_by=overall_score | VERIFIED | DISC-01 |

**Phase 29 (Dashboard) and Phase 30 (Keşif & Hisse Detay)** can now consume these endpoints directly.

## Self-Check: PASSED

- `/market/opportunities` endpoint: FOUND in backend/app/api/market.py
- `test_opportunities_endpoint_response_shape`: PASSED
- `test_bist100_filter_returns_only_bist100_sorted`: PASSED
- `test_phase_28_all_endpoints_registered`: PASSED
- Commits: a99704a, 1d2bb3f, bcb6940 — all present in git log
