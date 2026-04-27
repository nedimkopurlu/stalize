---
phase: 06-teknik-duzeltmeler
plan: 02
subsystem: api
tags: [asyncio, yfinance, run_in_executor, fastapi, diskcache, tdd]

requires:
  - phase: 02-ml-cache
    provides: "MLCA-02 diskcache result-level caching for get_ticker_history / get_ticker_info"

provides:
  - "async get_ticker_history wrapping yf.Ticker.history via run_in_executor"
  - "async get_ticker_info wrapping yf.Ticker.info via run_in_executor"
  - "non-blocking /api/macro/indicators endpoint via run_in_executor for yf.download"
  - "test_yfinance_async.py proving coroutine nature and thread offload"

affects:
  - 07-signal-quality
  - 09-data-model

tech-stack:
  added: []
  patterns:
    - "run_in_executor(None, sync_fn) for wrapping sync yfinance calls inside async handlers"
    - "TDD RED-GREEN: write failing coroutinefunction + thread-offload tests before implementation"

key-files:
  created:
    - backend/tests/test_yfinance_async.py
  modified:
    - backend/app/services/data_collector.py
    - backend/app/api/macro.py
    - backend/tests/test_yf_cache.py

key-decisions:
  - "run_in_executor(None, ...) uses asyncio default thread pool — no new pool needed (per 06-CONTEXT)"
  - "diskcache.get() remains synchronous (fast local disk, no HTTP) — only the Yahoo HTTP call is offloaded"
  - "yfinance imported at module level in macro.py — lazy import inside try block removed to allow patching"
  - "test_yf_cache.py converted to async def + await to stay compatible with async wrappers"
  - "httpx.ASGITransport used for FastAPI test client (httpx 0.28+ dropped app= kwarg)"

patterns-established:
  - "Pattern: Async wrapper = sync cache check + run_in_executor for the blocking I/O only"
  - "Pattern: Thread-name assertion proves run_in_executor offload (recorded_thread_name != MainThread)"

requirements-completed: [TECH-02]

duration: 4min
completed: 2026-04-19
---

# Phase 06 Plan 02: Async yfinance Wrappers Summary

**TECH-02 closed: yf.Ticker.history(), yf.Ticker.info, and yf.download() all offloaded to asyncio default thread pool via run_in_executor, proven by coroutinefunction assertions and a thread-name test**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-19T08:47:14Z
- **Completed:** 2026-04-19T08:51:19Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Converted `get_ticker_history` and `get_ticker_info` in `data_collector.py` to `async def`, wrapping the blocking Yahoo HTTP call with `asyncio.get_event_loop().run_in_executor(None, _fetch)`. Cache check remains synchronous (fast diskcache read, no I/O penalty).
- Updated 3 internal callers in `data_collector.py` (`initialize_stocks`, `_collect_stock_prices`, `collect_market_data`) to `await` the new coroutines.
- Replaced synchronous `yf.download()` in `get_macro_indicators()` with `await loop.run_in_executor(None, lambda: yf.download(...))`, moving `import yfinance as yf` to module level.
- Created `test_yfinance_async.py` with 5 tests: 2 coroutinefunction assertions, 2 executor end-to-end tests, 1 thread-offload test against the live FastAPI endpoint via `httpx.ASGITransport`.
- All 5 new tests GREEN; all 4 MLCA-02 cache regression tests (test_yf_cache.py) still pass; full suite 35 pass + 13 xpassed.

## Task Commits

1. **Task 1: RED tests for async yfinance wrappers** - `c73cbec4` (test)
2. **Task 2: Convert data_collector wrappers to async** - `b962883f` (feat)
3. **Task 3: Offload yf.download in macro indicators endpoint** - `78188d3a` (feat)

## Files Created/Modified

- `backend/tests/test_yfinance_async.py` — 5 TECH-02 tests: coroutinefunction assertions, executor plumbing, thread-offload proof
- `backend/app/services/data_collector.py` — `import asyncio`, `async def get_ticker_history`, `async def get_ticker_info`, 3 internal `await` callers
- `backend/app/api/macro.py` — `import asyncio` + `import yfinance as yf` at module level, `yf.download` wrapped with `run_in_executor`
- `backend/tests/test_yf_cache.py` — converted from sync to `async def` + `await` to work with the new async wrappers

## Decisions Made

- `run_in_executor(None, ...)` uses asyncio's default thread pool — no custom executor needed (per 06-CONTEXT decision).
- diskcache `.get()` stays synchronous — it is a local disk read with microsecond latency, no benefit in offloading.
- `import yfinance as yf` moved to module level in `macro.py` to allow `patch("app.api.macro.yf.download", ...)` — lazy imports inside function bodies cannot be patched at the module level.
- `httpx.ASGITransport` used instead of the deprecated `app=` kwarg (breaking change in httpx 0.28+).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_yf_cache.py to async def + await**
- **Found during:** Task 2 (converting data_collector wrappers to async)
- **Issue:** `test_yf_cache.py` called `dc.get_ticker_history` and `dc.get_ticker_info` as sync functions. After the async conversion these calls return coroutines without awaiting, making the tests collect coroutines instead of results — call_count and set_call assertions would silently pass on garbage values.
- **Fix:** Converted all 4 test functions to `async def` with `await` on both function calls.
- **Files modified:** `backend/tests/test_yf_cache.py`
- **Verification:** All 4 MLCA-02 cache tests pass (PASSED).
- **Committed in:** `b962883f` (Task 2 commit)

**2. [Rule 3 - Blocking] Fixed test httpx transport (ASGITransport)**
- **Found during:** Task 2 RED run of test 5
- **Issue:** `httpx.AsyncClient(app=fastapi_app, ...)` raises `TypeError: __init__() got an unexpected keyword argument 'app'` in httpx 0.28+.
- **Fix:** Changed to `httpx.ASGITransport(app=fastapi_app)` + `httpx.AsyncClient(transport=transport, ...)`.
- **Files modified:** `backend/tests/test_yfinance_async.py`
- **Verification:** test_macro_indicators_uses_executor passes.
- **Committed in:** `b962883f` (Task 2 commit)

**3. [Rule 3 - Blocking] Fixed yfinance patch target for lazy import**
- **Found during:** Task 2 RED run of test 5
- **Issue:** `patch("app.api.macro.yf.download", ...)` raised `ModuleNotFoundError: No module named 'app.api.macro.yf'` because `yf` was imported inside the try block (not at module level).
- **Fix:** Moved `import yfinance as yf` to module level in `macro.py` and used `patch("yfinance.download", ...)` (which patches the underlying module directly).
- **Files modified:** `backend/app/api/macro.py`, `backend/tests/test_yfinance_async.py`
- **Verification:** All tests pass including thread-offload assertion.
- **Committed in:** `78188d3a` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (1 Rule 1 bug, 2 Rule 3 blocking)
**Impact on plan:** All fixes necessary for test correctness and patching compatibility. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations above.

## Known Stubs

None — all wrappers fully wired and proven by tests.

## Next Phase Readiness

- TECH-02 closed: async yfinance foundation is clean.
- Phase 7 (signal quality) can rely on non-blocking data collection.
- Phase 9 (data model / signal history) can rely on non-blocking scoring pipeline.

---
*Phase: 06-teknik-duzeltmeler*
*Completed: 2026-04-19*
