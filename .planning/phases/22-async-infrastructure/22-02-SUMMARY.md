---
plan: 22-02
phase: 22-async-infrastructure
status: complete
requirements_satisfied:
  - ASYNC-03
  - ASYNC-04
---

# Plan 22-02 Summary: Scheduler Staggering + Startup Task Error Tracking

## What Was Done

**ASYNC-03 — Scheduler job staggering (main.py):**
- Added `timedelta` to datetime import
- Added `_now = datetime.now(timezone.utc)` once before all `add_job` calls
- Added `start_date=_now + timedelta(seconds=N)` to all 14 scheduler jobs with 30-second intervals:
  - background_kap_scan: 0s
  - background_tcmb_scan: 30s
  - background_tuik_scan: 60s
  - background_borsa_istanbul_scan: 90s
  - background_bist_datastore_scan: 120s
  - background_hmb_scan: 150s
  - background_takasbank_scan: 180s
  - background_mkk_scan: 210s
  - background_tefas_scan: 240s
  - background_dynamic_correlation: 270s
  - take_daily_snapshot: 300s
  - background_model_portfolio_generate: 330s
  - background_model_portfolio_snapshot: 360s
  - background_data_update (30min): 60s

**ASYNC-04 — Startup task error tracking (main.py):**
- Added module-level `_log_task_error(task: asyncio.Task)` function with `STARTUP_TASK_ERROR` log marker
- Replaced both bare `asyncio.create_task()` calls with tracked versions:
  ```python
  _task_startup_refresh = asyncio.create_task(startup_refresh_sources(), name="startup_refresh_sources")
  _task_startup_refresh.add_done_callback(_log_task_error)
  
  _task_initial_load = asyncio.create_task(data_collector.full_initial_load(), name="full_initial_load")
  _task_initial_load.add_done_callback(_log_task_error)
  ```

## Verification Results

```
start_date count in main.py → 14 ✓
add_done_callback count → 2 ✓
STARTUP_TASK_ERROR in main.py → 1 line ✓
timedelta in import → ✓
App import: python3 -c "from app.main import app, _log_task_error" → OK ✓
```
