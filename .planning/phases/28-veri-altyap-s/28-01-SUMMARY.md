---
phase: 28-veri-altyap-s
plan: "01"
subsystem: api
tags: [fastapi, router, forex, gold, bist100, testing, pytest, xfail]

requires: []

provides:
  - "market.py FastAPI router skeleton with /market/health endpoint"
  - "GOLD_COIN_WEIGHTS dict (gram/ons/ceyrek/yarim/tam 22-karat weights)"
  - "FOREX_PAIRS dict (6 TRY pairs: USD, EUR, GBP, CNY, JPY, CHF)"
  - "CURRENCY_PAIRS config updated with JPY/TRY and CHF/TRY entries"
  - "test_market_endpoints.py with 7 tests (3 green, 4 xfail pending Plans 28-02/03)"
  - "test_stocks_endpoint.py with 2 tests (1 green, 1 xfail pending Plan 28-03)"
  - "Session-scoped app_client fixture in conftest.py for TestClient sharing"

affects: [28-02, 28-03, 29-dashboard]

tech-stack:
  added: []
  patterns:
    - "Module-level TTL cache pattern (_market_cache, _market_cache_ttl) mirrors macro.py"
    - "Session-scoped TestClient in conftest.py to prevent APScheduler event loop collision across test modules"
    - "xfail(strict=False) for endpoint stubs — tests collect and run but don't fail CI until implemented"

key-files:
  created:
    - backend/app/api/market.py
    - backend/tests/test_market_endpoints.py
    - backend/tests/test_stocks_endpoint.py
  modified:
    - backend/app/core/config.py
    - backend/app/main.py
    - backend/tests/conftest.py

key-decisions:
  - "Session-scoped app_client in conftest.py rather than module-scoped per-file to avoid APScheduler + asyncpg event loop collision when two test modules use TestClient in same pytest run"
  - "xfail(strict=False) preserves RED state without blocking CI — XPASS is non-fatal when real data is present locally"
  - "FOREX_PAIRS uses Yahoo Finance ticker as key (USDTRY=X) and human label as value (USD/TRY) — consistent with downstream endpoint response shape"

patterns-established:
  - "market.py router pattern: module-level cache + GOLD_COIN_WEIGHTS + FOREX_PAIRS dicts defined before routes"
  - "Test scaffold convention: non-db constant tests pass green; db-dependent endpoint tests use xfail(strict=False)"

requirements-completed: [DASH-02]

duration: 5min
completed: "2026-05-04"
---

# Phase 28 Plan 01: Veri Altyapisi Infrastructure Summary

**Market domain router skeleton (market.py) with GOLD_COIN_WEIGHTS + FOREX_PAIRS constants, JPY/CHF config additions, and xfail test scaffolds for Plans 28-02/03 to implement against**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-04T19:26:46Z
- **Completed:** 2026-05-04T19:31:49Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `jpy_try: JPYTRY=X` and `chf_try: CHFTRY=X` to `CURRENCY_PAIRS` in config.py, bringing total TRY pairs to 6 (satisfies DASH-02 "5-10 pairs" requirement)
- Created `backend/app/api/market.py` with `APIRouter()`, `GOLD_COIN_WEIGHTS` (5 Turkish coin denominations), `FOREX_PAIRS` (6 TRY pairs), and `/market/health` probe; mounted in main.py
- Created test scaffolds in `test_market_endpoints.py` (7 tests) and `test_stocks_endpoint.py` (2 tests); 4 non-xfail tests pass green immediately, 5 xfail stubs waiting for Plans 28-02 and 28-03
- Fixed APScheduler + asyncpg event loop collision by adding session-scoped `app_client` fixture to conftest.py (Rule 1 auto-fix)

## Task Commits

1. **Task 1: Add JPY/TRY and CHF/TRY to CURRENCY_PAIRS config** - `37913c7` (feat)
2. **Task 2: Create market.py router skeleton and mount in main.py** - `13f794b` (feat)
3. **Task 3: Write RED test scaffolds for market endpoints and stocks bist100 filter** - `0ed438a` (test)

## Files Created/Modified

- `backend/app/api/market.py` - New market domain router with health probe, GOLD_COIN_WEIGHTS, FOREX_PAIRS constants
- `backend/tests/test_market_endpoints.py` - 7 tests: 3 green (health mount, coin weights, JPY/CHF pairs), 4 xfail endpoint stubs
- `backend/tests/test_stocks_endpoint.py` - 2 tests: 1 green (schema-only bist100 param check), 1 xfail (DISC-01 full sort verification)
- `backend/app/core/config.py` - Added jpy_try and chf_try to CURRENCY_PAIRS dict
- `backend/app/main.py` - Added market import and include_router call
- `backend/tests/conftest.py` - Added session-scoped app_client TestClient fixture

## Constants Available for Downstream Plans

**GOLD_COIN_WEIGHTS** (backend/app/api/market.py):
- gram: 1.0, ons: 31.1035, ceyrek: 1.754, yarim: 3.508, tam: 7.016

**FOREX_PAIRS** (backend/app/api/market.py):
- USDTRY=X: USD/TRY, EURTRY=X: EUR/TRY, GBPTRY=X: GBP/TRY, CNYTRY=X: CNY/TRY, JPYTRY=X: JPY/TRY, CHFTRY=X: CHF/TRY

## xfail Tests Waiting for Plans 28-02 and 28-03

| Test | File | Reason | Plan |
|------|------|--------|------|
| test_bist100_endpoint | test_market_endpoints.py | DASH-01 endpoint | 28-02 |
| test_forex_endpoint | test_market_endpoints.py | DASH-02 endpoint | 28-02 |
| test_gold_endpoint | test_market_endpoints.py | DASH-03 endpoint | 28-02 |
| test_opportunities_endpoint | test_market_endpoints.py | DISC-02 endpoint | 28-03 |
| test_bist100_filter | test_stocks_endpoint.py | DISC-01 live data | 28-03 |

## Decisions Made

- Session-scoped `app_client` in conftest.py rather than module-scoped per-file — prevents APScheduler + asyncpg event loop collision when two test modules use TestClient sequentially in the same pytest run
- `xfail(strict=False)` for endpoint stubs — tests collect and run but don't fail CI; XPASS is non-fatal if local DB already has data
- FOREX_PAIRS uses Yahoo Finance ticker as key (e.g., `USDTRY=X`) and human label as value (`USD/TRY`) — consistent with expected downstream endpoint response shape

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed cross-module TestClient event loop collision**
- **Found during:** Task 3 (test scaffolding)
- **Issue:** When test_market_endpoints.py and test_stocks_endpoint.py both create TestClient instances in the same pytest run, the first module's teardown closes the asyncpg event loop, causing `RuntimeError: Event loop is closed` at setup of the second module's TestClient
- **Fix:** Added session-scoped `app_client` fixture to conftest.py; both test modules delegate to it via module-scoped alias fixtures, so only one TestClient lifecycle exists per pytest session
- **Files modified:** backend/tests/conftest.py, backend/tests/test_market_endpoints.py, backend/tests/test_stocks_endpoint.py
- **Verification:** `pytest tests/test_market_endpoints.py tests/test_stocks_endpoint.py` passes with 4 passed, 4 xfailed, 1 xpassed (no ERRORs)
- **Committed in:** 0ed438a (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Essential for test suite correctness. No scope creep — fix confined to test infrastructure.

## Issues Encountered

- APScheduler + asyncpg event loop interaction is sensitive to multiple TestClient instances in the same pytest session. Session-scoped fixture is the standard pattern for this stack.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 28-02 and 28-03 can immediately start implementing endpoints against the existing xfail test contracts
- `GOLD_COIN_WEIGHTS` and `FOREX_PAIRS` constants are defined and stable — Plan 28-02 should import them directly from `app.api.market`
- `/market/health` endpoint is live and verifiable
- Existing test suite is unaffected (test_routers.py: 2 passed; pre-existing test_scheduler_overlap failure is unrelated)

---
*Phase: 28-veri-altyap-s*
*Completed: 2026-05-04*
