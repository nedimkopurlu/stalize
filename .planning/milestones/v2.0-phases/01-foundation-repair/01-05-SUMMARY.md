---
phase: 01-foundation-repair
plan: 05
subsystem: api
tags: [fastapi, apirouter, python, endpoint-split, domain-routing]

# Dependency graph
requires:
  - phase: 01-foundation-repair/01-02
    provides: scoring weights wired from config.py (FOND-02 complete)
  - phase: 01-foundation-repair/01-03
    provides: BASE_WEIGHTS removed from scoring engine (FOND-02 done)
  - phase: 01-foundation-repair/01-04
    provides: UTC datetime fix on model_portfolio (FOND-05 done)
provides:
  - 6 domain router files in backend/app/api/ (stocks, macro, portfolio, intelligence, causal, admin)
  - All 31 endpoints reachable via domain routers
  - endpoints.py deleted
  - main.py wired to 6 separate include_router calls
affects: [phase-02, phase-03, any future plan adding endpoints to api layer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Domain-based FastAPI APIRouter split: one file per business domain in app/api/"
    - "Lazy imports inside endpoint function bodies preserved verbatim (prevents circular imports)"
    - "main.py registers each domain router directly — no aggregator __init__.py"

key-files:
  created:
    - backend/app/api/stocks.py
    - backend/app/api/macro.py
    - backend/app/api/portfolio.py
    - backend/app/api/intelligence.py
    - backend/app/api/causal.py
    - backend/app/api/admin.py
  modified:
    - backend/app/main.py
  deleted:
    - backend/app/api/endpoints.py

key-decisions:
  - "D-07: 6 domain router files in backend/app/api/ (stocks, macro, portfolio, intelligence, causal, admin)"
  - "D-08: endpoints.py deleted entirely — content split verbatim into 6 domain files"
  - "D-09: main.py uses one app.include_router(x.router, prefix='/api') per domain router — no aggregator __init__.py"
  - "Lazy imports inside endpoint bodies kept lazy — prevents circular imports with services"

patterns-established:
  - "Pattern: Each domain router file starts with module docstring, strict imports, router = APIRouter(), logger = logging.getLogger(__name__)"
  - "Pattern: Pydantic models (e.g. PortfolioCreate) live in their domain router file"
  - "Pattern: Service imports that risk circular import stay lazy (inside function body)"

requirements-completed: [FOND-04]

# Metrics
duration: 15min
completed: 2026-04-17
---

# Phase 01 Plan 05: Router Split Summary

**933-line endpoints.py monolith split into 6 FastAPI domain routers (stocks, macro, portfolio, intelligence, causal, admin) with all 31 endpoints reachable and full test suite green**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-17T05:13:01Z
- **Completed:** 2026-04-17T05:28:00Z
- **Tasks:** 2 completed
- **Files modified:** 8 (6 created, 1 modified, 1 deleted)

## Accomplishments

- Created 6 domain router files totalling 935 lines of migrated endpoint code
- Deleted the 933-line endpoints.py monolith entirely
- Updated main.py to import and register 6 separate domain routers
- All 9 tests pass — FOND-04 xfail tests (test_endpoints_py_deleted, test_all_routes_registered) now XPASS
- App starts cleanly with 36 routes registered (31 domain + 5 FastAPI internal)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 6 domain router files migrating from endpoints.py** - `b2e85df` (feat)
2. **Task 2: Update main.py to use 6 domain routers, delete endpoints.py** - `b4ca9a7` (feat)

## Files Created/Modified

- `backend/app/api/stocks.py` — 8 endpoints: list/detail/prices/technical/run-analysis/rankings/sectors/scoring-update
- `backend/app/api/macro.py` — 3 endpoints: TCMB scan, TUIK scan, macro events feed
- `backend/app/api/portfolio.py` — 4 endpoints: GET/POST/DELETE portfolio + model-portfolio; includes PortfolioCreate model
- `backend/app/api/intelligence.py` — 7 endpoints: intelligence overview/fusion/impact-ranking + 4 correlation endpoints
- `backend/app/api/causal.py` — 6 endpoints: feed/scenarios/scenario/triggers/stock-causal/run-all
- `backend/app/api/admin.py` — 3 endpoints: health-check, KAP scan trigger, dashboard summary
- `backend/app/main.py` — replaced single endpoints import+include_router with 6 domain-specific calls
- `backend/app/api/endpoints.py` — DELETED

## Decisions Made

- Lazy imports inside endpoint function bodies kept lazy (verbatim copy from endpoints.py) — prevents circular imports per D-09 and RESEARCH anti-pattern guidance
- PortfolioCreate Pydantic model moved to portfolio.py (the only file that uses it)
- health_check, kap/scan, and dashboard all placed in admin.py (operational concerns, not domain data)
- No api/__init__.py aggregator created per D-09

## Deviations from Plan

None — plan executed exactly as written. All 6 files created, endpoints.py deleted, main.py updated, full test suite green.

## Issues Encountered

None — the venv Python was at `.venv/bin/python` (not in system PATH), confirmed working before commits.

## Known Stubs

None — no placeholder data or hardcoded stubs introduced. All endpoints are verbatim copies of production code from endpoints.py.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 01 Foundation Repair is now complete: all 5 FOND requirements addressed across plans 01-05
- Phase 02 can proceed: data pipelines, scoring, and endpoints are all on a clean, trustworthy foundation
- Each domain router is independently navigable and testable
- Adding new endpoints: add to the appropriate domain router file in backend/app/api/

---
*Phase: 01-foundation-repair*
*Completed: 2026-04-17*
