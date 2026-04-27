---
phase: 07-sinyal-kalitesi
plan: "03"
subsystem: backend
tags: [sgnl-02, volume-ratio, api, tdd, signal-quality]
dependency_graph:
  requires: [07-01]
  provides: [volume_ratio field on GET /api/stocks, compute_volume_ratio helper]
  affects: [frontend stock table, tooltip display]
tech_stack:
  added: []
  patterns: [window function subquery for batched aggregate, session-scoped pytest event loop]
key_files:
  created: []
  modified:
    - backend/app/services/technical.py
    - backend/app/api/stocks.py
    - backend/tests/test_signal_quality.py
    - backend/tests/conftest.py
    - backend/pytest.ini
decisions:
  - "Session-scoped asyncio event loop in conftest prevents asyncpg cross-loop errors when multiple DB async tests run sequentially"
  - "asyncio_default_test_loop_scope = session in pytest.ini ensures pytest-asyncio 1.x uses the session fixture"
  - "row_number() window subquery approach used for batched 20-day avg volume — single SQL round-trip regardless of list size"
metrics:
  duration_minutes: 3
  completed_date: "2026-04-19"
  tasks_completed: 2
  files_modified: 5
---

# Phase 07 Plan 03: Volume Ratio (SGNL-02) Summary

**One-liner:** volume_ratio field added to GET /api/stocks via row_number() window subquery batching 20-day avg volume per stock, with session-scoped asyncio event loop fix to eliminate cross-loop asyncpg errors.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add compute_volume_ratio pure helper | ea4f72e5 | backend/app/services/technical.py, backend/tests/test_signal_quality.py |
| 2 | Compute per-stock 20-day avg volume and surface volume_ratio on GET /api/stocks | 01c1d233 | backend/app/api/stocks.py, backend/tests/test_signal_quality.py, backend/tests/conftest.py, backend/pytest.ini |

## Verification Results

- `python3 -m pytest tests/test_signal_quality.py` → **11 passed, 0 failed**
- `python3 -m pytest -x` (full suite) → **46 passed, 13 xpassed, 0 failed**
- `compute_volume_ratio(2_400_000, 1_000_000) == 2.4` — PASS
- `compute_volume_ratio(1_000_000, None) is None` — PASS
- `compute_volume_ratio(1_000_000, 0) is None` — PASS
- `grep -c "def compute_volume_ratio" technical.py` → 1 (module-level, not inside class)
- `grep -c '"volume_ratio"' stocks.py` → 1
- `grep -c "compute_volume_ratio" stocks.py` → 2 (import + call)
- `grep -c 'row_number' stocks.py` → 1 (batched query present)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Infrastructure] Session-scoped asyncio event loop for async test suite**
- **Found during:** Task 2 verification
- **Issue:** `test_technical_endpoint_includes_stop_loss_and_target` (SGNL-01 from 07-02) creates an AsyncSessionLocal backed by asyncpg. When its function-scoped event loop closes after the test, asyncpg pool connections remain bound to that loop. Our SGNL-02 test (`test_stocks_list_includes_volume_ratio_key`) starts a fresh event loop and the FastAPI app tries to use the pool from the old loop, raising `RuntimeError: Task got Future attached to a different loop`.
- **Fix:** Added `session`-scoped `event_loop` fixture to `conftest.py` so all async tests share one event loop. Added `asyncio_default_test_loop_scope = session` and `asyncio_default_fixture_loop_scope = session` to `pytest.ini` to ensure pytest-asyncio 1.x picks up the session fixture.
- **Files modified:** `backend/tests/conftest.py`, `backend/pytest.ini`
- **Commit:** 01c1d233

## Known Stubs

None — `volume_ratio` is fully computed from real DB data (20-day avg via SQL window function) and returned in every GET /api/stocks response.

## Self-Check: PASSED

- `backend/app/services/technical.py` — FOUND, contains `def compute_volume_ratio`
- `backend/app/api/stocks.py` — FOUND, contains `volume_ratio` field and `row_number` subquery
- `backend/tests/conftest.py` — FOUND, contains session-scoped `event_loop` fixture
- `backend/pytest.ini` — FOUND, contains `asyncio_default_test_loop_scope = session`
- Commit `ea4f72e5` — FOUND (Task 1)
- Commit `01c1d233` — FOUND (Task 2)
