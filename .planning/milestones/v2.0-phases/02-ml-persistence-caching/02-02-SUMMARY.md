---
phase: 02-ml-persistence-caching
plan: 02
subsystem: ml-persistence
tags: [xgboost, joblib, model-persistence, apscheduler, preload, retrain]

# Dependency graph
requires:
  - phase: 02-ml-persistence-caching
    plan: 01
    provides: TDD stub infrastructure (test_ml_persistence.py RED stubs, models/ dir, diskcache installed)
provides:
  - MLAnalysisEngine save/load/preload/retrain methods
  - ml_engine singleton in ml.py
  - Startup model preload in lifespan
  - Weekly APScheduler retrain cron job
affects:
  - backend/app/services/ml.py
  - backend/app/main.py

# Tech stack
tech_stack:
  added:
    - libomp (installed via brew — required for xgboost 2.1.4 on macOS arm64)
  patterns:
    - Per-stock XGBoost model persistence: {SYMBOL}_xgb.ubj + {SYMBOL}_scaler.joblib pairs
    - In-memory model cache: self._models dict on MLAnalysisEngine singleton
    - Startup preload before scheduler.start() in lifespan
    - APScheduler cron trigger for Sunday 02:00 weekly retrain

# Key files
key_files:
  modified:
    - backend/app/services/ml.py
    - backend/app/main.py
    - backend/tests/test_ml_persistence.py

# Key decisions
decisions:
  - "MODEL_DIR uses os.path.abspath(__file__-anchored) to resolve correctly regardless of uvicorn launch directory"
  - "ml_engine singleton at module bottom — avoids circular imports; lifespan imports lazily"
  - "patch('app.core.database.AsyncSessionLocal') in test_weekly_retrain_job — because AsyncSessionLocal is lazily imported inside background_xgb_retrain function body, not at module scope"
  - "libomp installed via brew (deviation Rule 3) — required for xgboost 2.1.4 on macOS; already in project requirements.txt"

# Metrics
metrics:
  duration: 11 minutes
  completed: "2026-04-17"
  tasks_completed: 2
  files_modified: 3
---

# Phase 02 Plan 02: XGBoost Model Persistence (MLCA-01) Summary

**One-liner:** XGBoost per-stock model persistence with .ubj+.joblib pairs, startup preload via lifespan, and weekly APScheduler retrain — 4 MLCA-01 tests GREEN.

## What Was Built

### Task 1: MLAnalysisEngine save/load/preload/retrain_and_save (feat(02-02) f21c986)

Refactored `backend/app/services/ml.py`:

- Added `import os` and `import joblib`
- Added `MODEL_DIR` module-level constant anchored to `__file__` (resolves to `backend/models/`)
- Added `self._models: dict = {}` to `__init__`
- Added `_model_path(symbol)` and `_scaler_path(symbol)` path helpers
- Added `save_model(symbol, model, scaler)`: writes `{SYMBOL}_xgb.ubj` + `{SYMBOL}_scaler.joblib`
- Added `load_model(symbol)`: returns `(XGBRegressor, StandardScaler)` or `(None, None)`
- Added `preload_all_models()`: scans MODEL_DIR for `*.ubj`, loads all into `_models`
- Added `retrain_and_save(db, stock)`: force retrain + overwrite disk artifacts
- Refactored `_train_and_predict` to check `_models` cache before training from scratch
- Updated `analyze_stock` to pass `symbol=stock.symbol` to `_train_and_predict`
- Added `ml_engine = MLAnalysisEngine()` module-level singleton

### Task 2: main.py startup preload + weekly APScheduler job (feat(02-02) c46971f)

Updated `backend/app/main.py`:

- Added `import asyncio`
- Added `background_xgb_retrain()` async function (queries active stocks, calls `ml_engine.retrain_and_save` per stock with `asyncio.sleep(0)` yield between stocks)
- Added preload block in lifespan BEFORE `scheduler.start()`: calls `ml_engine.preload_all_models()`
- Added `scheduler.add_job(background_xgb_retrain, "cron", day_of_week="sun", hour=2, minute=0)`

Replaced 4 `pytest.fail` stubs in `backend/tests/test_ml_persistence.py` with real tests:
- `test_save_creates_files`: verifies .ubj + .joblib created in tmpdir
- `test_load_restores_model`: verifies loaded model+scaler usable for prediction without refit
- `test_first_run_saves_model`: async test verifying first analyze_stock call saves both files
- `test_weekly_retrain_job`: async test verifying retrain_and_save called per active stock

## Test Results

```
tests/test_ml_persistence.py::test_save_creates_files PASSED
tests/test_ml_persistence.py::test_load_restores_model PASSED
tests/test_ml_persistence.py::test_first_run_saves_model PASSED
tests/test_ml_persistence.py::test_weekly_retrain_job PASSED
4 passed — MLCA-01 GREEN
```

**Full suite:** 7 passed, 6 xpassed, 7 failed (all MLCA-02/MLCA-03 stubs — expected, unchanged from pre-plan baseline).

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 | f21c986 | backend/app/services/ml.py |
| 2 | c46971f | backend/app/main.py, backend/tests/test_ml_persistence.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] libomp not installed — XGBoost failed to load**
- **Found during:** Task 1 test execution
- **Issue:** `xgboost.core.XGBoostError: Library not loaded: @rpath/libomp.dylib` — OpenMP runtime missing on macOS
- **Fix:** `brew install libomp` (libomp is listed as a system dependency for xgboost on macOS; already in project requirements.txt implicitly via xgboost==2.1.4)
- **Files modified:** None (system-level install)
- **Commit:** N/A (system install, no source change)

**2. [Rule 1 - Bug] test_weekly_retrain_job patch target was wrong**
- **Found during:** Task 2 test execution
- **Issue:** Plan's example code used `patch("app.main.AsyncSessionLocal")` but `AsyncSessionLocal` is imported lazily inside `background_xgb_retrain`'s function body, not at `app.main` module scope. `patch("app.main.AsyncSessionLocal")` raised `AttributeError: module has no attribute 'AsyncSessionLocal'`
- **Fix:** Changed patch target to `app.core.database.AsyncSessionLocal` — the actual module where `AsyncSessionLocal` is defined and imported from
- **Files modified:** backend/tests/test_ml_persistence.py
- **Commit:** c46971f

## Known Stubs

None — all files modified in this plan have real implementations, no placeholders.

## Self-Check: PASSED
