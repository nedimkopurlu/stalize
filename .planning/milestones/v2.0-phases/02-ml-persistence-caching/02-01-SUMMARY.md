---
phase: 02-ml-persistence-caching
plan: 01
subsystem: testing
tags: [pytest, diskcache, tdd, ml-persistence, yfinance-cache, llm-cache, xgboost]

# Dependency graph
requires:
  - phase: 01-foundation-repair
    provides: Clean backend foundation with working tests, scoring, and router structure
provides:
  - 11 pytest.fail() stubs establishing the full Phase 2 test contract (RED phase)
  - backend/models/ directory tracked in git for XGBoost model file storage
  - diskcache==5.6.3 pinned in requirements.txt
  - .gitignore entries excluding generated *.ubj, *.joblib, and cache/ directories
affects:
  - 02-02 (ML persistence implementation turns MLCA-01 stubs GREEN)
  - 02-03 (yfinance cache implementation turns MLCA-02 stubs GREEN)
  - 02-04 (LLM cache implementation turns MLCA-03 stubs GREEN)

# Tech tracking
tech-stack:
  added: [diskcache==5.6.3]
  patterns:
    - TDD RED phase with pytest.fail() stubs — no production code, guarantees stubs cannot accidentally pass
    - .gitkeep to track empty directories in git
    - .gitignore to exclude generated runtime artifacts from version control

key-files:
  created:
    - backend/tests/test_ml_persistence.py
    - backend/tests/test_yf_cache.py
    - backend/tests/test_llm_cache.py
    - backend/models/.gitkeep
    - backend/.gitignore
  modified:
    - backend/requirements.txt

key-decisions:
  - "Plain pytest.fail() over @pytest.mark.xfail for RED stubs — guarantees tests cannot accidentally pass before implementation"
  - "diskcache==5.6.3 pinned; joblib NOT added (already transitive via scikit-learn==1.6.1)"
  - "No production imports in stub files — avoids import errors from non-existent cache infrastructure"

patterns-established:
  - "Phase 2 TDD contract: all 11 stubs RED, implementation plans make them GREEN one-by-one"

requirements-completed: [MLCA-01, MLCA-02, MLCA-03]

# Metrics
duration: 5min
completed: 2026-04-17
---

# Phase 02 Plan 01: ML Persistence + Caching — TDD Stubs (RED Phase) Summary

**11 pytest.fail() stubs establishing the full MLCA-01/02/03 test contract; diskcache==5.6.3 added; backend/models/ scaffolded**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-17T00:00:00Z
- **Completed:** 2026-04-17T00:05:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added `diskcache==5.6.3` to backend/requirements.txt and created backend/.gitignore with entries for model and cache artifact directories
- Created `backend/models/.gitkeep` so the XGBoost model output directory is tracked in git
- Wrote 11 `pytest.fail()` stubs across 3 test files confirming RED before any implementation begins
- Verified Phase 1 tests remain green (3 passed, 6 xpassed) — stubs cause no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add diskcache dependency and scaffold directories** - `0023480` (chore)
2. **Task 2: Write failing test stubs for MLCA-01, MLCA-02, MLCA-03 (RED phase)** - `2d64458` (test)

**Plan metadata:** _(docs commit to follow)_

## Files Created/Modified

- `backend/requirements.txt` — Added `diskcache==5.6.3` under Machine Learning section
- `backend/.gitignore` — Excludes `models/*.ubj`, `models/*.joblib`, `cache/` from git
- `backend/models/.gitkeep` — Empty file so git tracks the models output directory
- `backend/tests/test_ml_persistence.py` — 4 stubs for MLCA-01 (save, load, first-run, weekly retrain)
- `backend/tests/test_yf_cache.py` — 4 stubs for MLCA-02 (cache hit, price TTL, info TTL, empty guard)
- `backend/tests/test_llm_cache.py` — 3 stubs for MLCA-03 (cache hit, key format, expiry)

## Decisions Made

- Plain `pytest.fail()` used instead of `@pytest.mark.xfail` — ensures stubs are unconditionally RED with no risk of accidental pass
- `joblib` was NOT added to requirements.txt — it is already a transitive dependency via scikit-learn==1.6.1
- Production module imports omitted from stub files — avoids import errors since diskcache infrastructure does not exist yet

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Known Stubs

All 11 test functions in this plan ARE the intentional stubs. They exist to define the test contract. The following plans will resolve them:

| Stub file | Tests | Resolved by |
|-----------|-------|-------------|
| test_ml_persistence.py | 4 (MLCA-01) | 02-02-PLAN.md |
| test_yf_cache.py | 4 (MLCA-02) | 02-03-PLAN.md |
| test_llm_cache.py | 3 (MLCA-03) | 02-04-PLAN.md |

These stubs are intentional RED placeholders, not accidental gaps.

## Next Phase Readiness

- Phase 2 test contract fully established — all 11 tests RED, zero import errors
- backend/models/ directory ready to receive XGBoost .ubj files after 02-02 implementation
- diskcache available for cache implementation in 02-03 and 02-04
- Ready to execute 02-02-PLAN.md (ML model save/load implementation)

---
*Phase: 02-ml-persistence-caching*
*Completed: 2026-04-17*
