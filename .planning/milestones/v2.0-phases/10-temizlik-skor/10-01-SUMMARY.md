---
plan: 10-01
phase: 10
subsystem: backend
tags: [cleanup, llm-removal, causal-removal, deletion]
dependency_graph:
  requires: []
  provides: [clean-main-no-llm-causal, AIRF-01, AIRF-02]
  affects: [backend/app/main.py, backend/app/models/__init__.py]
tech_stack:
  added: []
  patterns: [deletion-first, import-cleanup]
key_files:
  created: []
  modified:
    - backend/app/main.py
    - backend/app/models/__init__.py
  deleted:
    - backend/app/services/llm_sentiment.py
    - backend/app/services/briefing_generator.py
    - backend/app/api/briefing.py
    - backend/app/models/model_daily_briefing.py
    - backend/tests/test_daily_briefing.py
    - backend/tests/test_llm_cache.py
    - backend/tests/test_llm_infrastructure.py
    - backend/app/services/knowledge_graph.py
    - backend/app/services/causal.py
    - backend/app/services/event_fusion.py
    - backend/app/api/causal.py
decisions:
  - "DailyBriefing removed from models/__init__.py exports — model_daily_briefing.py deleted so import was blocking test collection"
  - "CausalChainLog retained in geopolitics.py — it is a DB model unrelated to causal engine logic"
metrics:
  duration: "3 minutes"
  completed_date: "2026-04-20"
  tasks: 2
  files_modified: 2
  files_deleted: 11
requirements_satisfied: [AIRF-01, AIRF-02]
---

# Phase 10 Plan 01: LLM ve Causal Engine Kaldırma Summary

**One-liner:** Deleted 11 LLM/causal files and purged all briefing/causal imports, scheduler jobs, and router registrations from main.py.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | LLM dosyalarini sil ve main.py'den LLM referanslarini kaldir | b9ace17c | 7 deleted, main.py modified |
| 2 | Causal engine dosyalarini sil ve main.py'den causal referanslarini kaldir | 08275cd2 | 4 deleted, main.py + models/__init__.py modified |

## Deleted Files

### LLM / Briefing (Task 1)
- `backend/app/services/llm_sentiment.py` — DeepSeek LLM sentiment service
- `backend/app/services/briefing_generator.py` — Daily briefing pipeline
- `backend/app/api/briefing.py` — /api/briefing/* router
- `backend/app/models/model_daily_briefing.py` — DailyBriefing SQLAlchemy model
- `backend/tests/test_daily_briefing.py`
- `backend/tests/test_llm_cache.py`
- `backend/tests/test_llm_infrastructure.py`

### Causal Engine (Task 2)
- `backend/app/services/knowledge_graph.py` — Causal knowledge graph (was untracked)
- `backend/app/services/causal.py` — Causal engine service (was untracked)
- `backend/app/services/event_fusion.py` — Event fusion pipeline
- `backend/app/api/causal.py` — /api/causal/* router

## Changes to main.py

- Import line updated: `stocks, macro, portfolio, intelligence, admin` (removed `causal`, `briefing`)
- Removed top-level `scheduler.add_job(generate_daily_briefing, ...)` cron job
- Removed `background_macro_scan` function (called `causal_engine.run_realtime_scenarios`)
- Removed `background_event_fusion` function (called `run_event_fusion`)
- Removed lifespan `scheduler.add_job(background_macro_scan, ...)` call
- Removed lifespan `scheduler.add_job(background_event_fusion, ...)` call
- Removed `app.include_router(causal.router, prefix="/api")`
- Removed `app.include_router(briefing.router, prefix="/api")`
- Updated FastAPI description: "Teknik + Temel + Haber Analizi ile BIST100 hisse analizi"

## Remaining Tests

- `test_scoring.py` — PASSED (11 passed, 3 xpassed)
- `test_signal_quality.py` — PASSED (included in above run)
- `from app.main import app` — imports cleanly, no errors

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Import] Fixed models/__init__.py still importing deleted DailyBriefing**
- **Found during:** Task 2 verification (test_signal_quality.py collection error)
- **Issue:** `app/models/__init__.py` had `from app.models.model_daily_briefing import DailyBriefing` which caused `ModuleNotFoundError` on test collection
- **Fix:** Removed the import and `"DailyBriefing"` from `__all__` in `models/__init__.py`
- **Files modified:** `backend/app/models/__init__.py`
- **Commit:** 08275cd2

## Known Stubs

None — this plan is pure deletion, no new features introduced.

## Self-Check: PASSED

- main.py exists and imports cleanly
- 11 deleted files confirmed absent from filesystem
- test_scoring.py and test_signal_quality.py: 11 passed, 3 xpassed
- Commits b9ace17c and 08275cd2 exist in git log
