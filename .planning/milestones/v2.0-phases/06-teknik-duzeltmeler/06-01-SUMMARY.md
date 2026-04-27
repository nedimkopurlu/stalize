---
phase: 06-teknik-duzeltmeler
plan: "01"
subsystem: backend-scheduler
tags: [apscheduler, overlap-protection, tech-debt, cron, interval]
dependency_graph:
  requires: []
  provides: [TECH-01]
  affects: [backend/app/main.py, APScheduler job store]
tech_stack:
  added: []
  patterns: [APScheduler max_instances=1, APScheduler misfire_grace_time=300, TDD red-green]
key_files:
  created:
    - backend/tests/test_scheduler_overlap.py
  modified:
    - backend/app/main.py
decisions:
  - "Kwargs added literally at each call site (not via helper wrapper) — ensures grep -c 'max_instances=1' main.py == 10 as required by TECH-01 contract"
  - "Module-level generate_daily_briefing job and all 9 lifespan jobs share the same two kwargs — no exceptions"
  - "TDD workflow used: RED commit first, GREEN commit after all 10 sites updated"
metrics:
  duration: "~12 minutes"
  completed_date: "2026-04-19"
  tasks_completed: 2
  files_modified: 2
---

# Phase 6 Plan 01: APScheduler Overlap Protection Summary

One-liner: APScheduler overlap protection via explicit `max_instances=1, misfire_grace_time=300` on all 10 `add_job()` sites in `main.py`, enforced by parametrized pytest.

## Objective Achieved

TECH-01 closed: every APScheduler job in `backend/app/main.py` now carries `max_instances=1` and `misfire_grace_time=300`, preventing two back-to-back fires of the same cron/interval job from running concurrently.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Write failing test asserting max_instances and misfire_grace | `3125b9b6` | backend/tests/test_scheduler_overlap.py |
| 2 (GREEN) | Add kwargs to all 10 scheduler.add_job() calls in main.py | `66a5745c` | backend/app/main.py |

## What Was Done

### Task 1 - RED Test

Created `backend/tests/test_scheduler_overlap.py` with 3 tests:

- `test_all_jobs_have_max_instances_one`: Starts FastAPI lifespan via ASGI transport, enumerates all jobs via `scheduler.get_jobs()`, fails if any job's `max_instances` is not `1`.
- `test_all_jobs_have_misfire_grace`: Same lifespan pattern, fails if any job's `misfire_grace_time` is not `300`.
- `test_module_level_briefing_job_registered`: Imports `scheduler` directly at import time (no lifespan needed), verifies the module-level `generate_daily_briefing` job carries both attrs.

All 3 tests failed RED before main.py was updated (max_instances was `None` on all jobs).

### Task 2 - GREEN Implementation

Added `max_instances=1, misfire_grace_time=300` to all 10 `scheduler.add_job()` call sites:

1. Module-level: `generate_daily_briefing` cron (06:30 Europe/Istanbul, mon-fri)
2. Lifespan: `background_macro_scan` interval 1h
3. Lifespan: `background_kap_scan` interval `settings.KAP_SCAN_INTERVAL_MIN`
4. Lifespan: `background_tcmb_scan` interval 2h
5. Lifespan: `background_tuik_scan` cron mon-fri 09:00
6. Lifespan: `background_event_fusion` interval 1h
7. Lifespan: `background_dynamic_correlation` cron mon 09:30
8. Lifespan: `background_audit_and_learn` cron mon-fri 18:05
9. Lifespan: `background_model_portfolio_generation` cron mon-fri 18:15
10. Lifespan: `background_xgb_retrain` cron sun 02:00

## Verification

```
grep -c "max_instances=1" backend/app/main.py    → 10
grep -c "misfire_grace_time=300" backend/app/main.py → 10
grep -c "scheduler.add_job" backend/app/main.py  → 10

pytest tests/test_scheduler_overlap.py -v        → 3 passed
pytest tests/test_daily_briefing.py tests/test_models.py tests/test_scoring.py
      tests/test_routers.py tests/test_kap_parser.py tests/test_llm_cache.py
      tests/test_llm_infrastructure.py            → 13 passed, 13 xpassed
```

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - no stubs introduced. All 10 job registrations are fully wired.

## Self-Check: PASSED

- `backend/tests/test_scheduler_overlap.py` exists: FOUND
- `backend/app/main.py` has `max_instances=1` x10: FOUND
- Commit `3125b9b6` (RED test): FOUND
- Commit `66a5745c` (GREEN implementation): FOUND
