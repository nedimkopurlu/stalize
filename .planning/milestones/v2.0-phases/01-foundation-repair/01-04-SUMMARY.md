---
phase: 01-foundation-repair
plan: 04
subsystem: database
tags: [sqlalchemy, datetime, timezone, postgresql, timestamptz]

# Dependency graph
requires:
  - phase: 01-foundation-repair
    provides: reference pattern from stock.py using DateTime(timezone=True) + func.now()
provides:
  - ModelPortfolioHistory with timezone-aware DateTime columns (generation_date, target_date)
  - FOND-05 requirement fulfilled — no naive UTC timestamps in any model file
affects: [02-data-pipeline, any phase writing ModelPortfolioHistory records]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DateTime(timezone=True) + server_default=func.now() for all model timestamp columns"
    - "Remove Python-side datetime.utcnow defaults — push to DB server via func.now()"

key-files:
  created: []
  modified:
    - backend/app/models/model_portfolio.py

key-decisions:
  - "Removed 'from datetime import datetime' entirely — replaced with sqlalchemy.sql.func pattern"
  - "Added inline developer comment about ALTER TABLE requirement for existing dev DBs (create_all does not alter existing columns)"
  - "generation_date gets server_default=func.now(); target_date is nullable (no server_default — value supplied at write time)"

patterns-established:
  - "All models now uniformly use DateTime(timezone=True) — no naive DateTime columns remain"

requirements-completed: [FOND-05]

# Metrics
duration: 8min
completed: 2026-04-17
---

# Phase 01 Plan 04: Fix Naive DateTime Columns in model_portfolio.py Summary

**ModelPortfolioHistory.generation_date and target_date migrated from bare DateTime + datetime.utcnow to DateTime(timezone=True) + server_default=func.now(), eliminating naive UTC timestamps across all model files**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-17T10:10:15Z
- **Completed:** 2026-04-17T10:18:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Fixed ModelPortfolioHistory.generation_date: `DateTime` -> `DateTime(timezone=True)`, `default=datetime.utcnow` -> `server_default=func.now()`
- Fixed ModelPortfolioHistory.target_date: `DateTime` -> `DateTime(timezone=True)`
- Removed `from datetime import datetime` import (no longer needed)
- Added `from sqlalchemy.sql import func` import (matches stock.py pattern)
- Added inline developer note about manual ALTER TABLE SQL for existing dev DBs
- FOND-05 test_model_portfolio_timezone goes from XFAIL to XPASS
- All models now uniformly use timezone-aware DateTime columns

## Task Commits

Each task was committed atomically:

1. **Task 1: FOND-05 — Fix DateTime columns in model_portfolio.py** - `bcf00f6` (feat)

**Plan metadata:** (docs commit — see final state update)

## Files Created/Modified
- `backend/app/models/model_portfolio.py` — DateTime(timezone=True) + func.now() pattern applied; naive datetime.utcnow removed

## Decisions Made
- Followed the established stock.py pattern exactly: `DateTime(timezone=True)` + `server_default=func.now()` for generation_date, `DateTime(timezone=True)` only for target_date (no server_default — value is application-supplied)
- Added developer migration note as inline comment (D-14 from CONTEXT.md: no Alembic migration for this phase)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The fix was a straightforward 3-change edit: replace import, fix generation_date column, fix target_date column.

## User Setup Required

**Existing dev DB:** If `model_portfolio_history` table already exists with `timestamp without time zone` columns, run this SQL manually (create_all() does NOT alter existing columns):

```sql
ALTER TABLE model_portfolio_history ALTER COLUMN generation_date TYPE TIMESTAMPTZ;
ALTER TABLE model_portfolio_history ALTER COLUMN target_date TYPE TIMESTAMPTZ;
```

This note is also embedded as a comment directly in model_portfolio.py.

## Known Stubs

None.

## Next Phase Readiness
- All FOND-05 requirements satisfied — no naive UTC timestamps in any backend model file
- FOND-04 (router split) remains the only incomplete Phase 01 requirement (2 tests still XFAIL)
- Service layer scan for datetime.utcnow() was noted in D-13 but no occurrences were found (kap_parser.py was already fixed in plan 01-02)

---
*Phase: 01-foundation-repair*
*Completed: 2026-04-17*
