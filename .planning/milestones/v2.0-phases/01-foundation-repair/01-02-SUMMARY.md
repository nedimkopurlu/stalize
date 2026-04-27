---
phase: 01-foundation-repair
plan: 02
subsystem: backend
tags: [feedparser, kap, requirements, ml-cleanup, tdd, pytest]

# Dependency graph
requires:
  - phase: 01-foundation-repair/01-01
    provides: Test stubs (xfail) for FOND-01/02/04/05

provides:
  - requirements.txt without tensorflow/torch/transformers/sentencepiece (~3-4GB removed)
  - kap_parser.py with all mock data paths deleted and feedparser hard-imported
  - main.py with feedparser startup RuntimeError guard in lifespan()
  - FOND-01 passing tests (3/3 green)

affects:
  - 01-03 scoring-weights (clean foundation)
  - 01-04 router-split (main.py changes reference)
  - 01-05 utc-timestamps (datetime.utcnow fixes started here)

# Tech tracking
tech-stack:
  added: [pytest, pytest-asyncio]
  patterns:
    - Hard import pattern for required dependencies (no try/except guards)
    - Startup validation guard in lifespan() for critical dependencies
    - Return [] + WARNING log for transient network failures (not mock data)
    - datetime.now(timezone.utc) instead of datetime.utcnow() throughout

key-files:
  created:
    - backend/tests/test_kap_parser.py
  modified:
    - backend/requirements.txt
    - backend/app/services/kap_parser.py
    - backend/app/main.py

key-decisions:
  - "FOND-03: tensorflow, torch, transformers, sentencepiece removed from requirements.txt — confirmed unused, vaderSentiment independent"
  - "FOND-01: feedparser hard-imported at module top — ModuleNotFoundError propagates on startup, no silent fallback"
  - "FOND-01: KAP network failures return [] + WARNING, never mock data"
  - "FOND-01: _generate_mock_announcements deleted entirely — not merely unreachable"
  - "datetime.utcnow() fixed to datetime.now(timezone.utc) in all 4 occurrences in kap_parser.py"

patterns-established:
  - "Hard import for required deps: import feedparser at module top — no try/except"
  - "Transient failure pattern: except Exception -> WARNING log + return [] (not mock, not error)"
  - "Startup validation: try/except in lifespan() raises RuntimeError with install instructions"

requirements-completed: [FOND-01, FOND-03]

# Metrics
duration: 8min
completed: 2026-04-17
---

# Phase 01 Plan 02: ML Dependency Cleanup + KAP Mock Deletion Summary

**Removed 3-4GB of unused ML packages from requirements.txt and deleted all KAP mock data paths from kap_parser.py, replacing them with real failure semantics (hard import + WARNING + empty list return)**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-17T05:03:24Z
- **Completed:** 2026-04-17T05:11:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Removed tensorflow==2.19.0, torch==2.6.0, transformers==4.51.3, sentencepiece==0.2.0 from requirements.txt — ~3-4GB dependency overhead eliminated
- Deleted `_generate_mock_announcements()` method entirely (38 lines of fake data gone)
- Replaced all 3 mock fallback paths in `fetch_latest_announcements()` with correct semantics: hard import, no None guard, empty list on network failure
- Added feedparser startup RuntimeError guard in `lifespan()` — missing feedparser fails fast with clear install instructions
- Fixed all `datetime.utcnow()` calls (4 occurrences) to `datetime.now(timezone.utc)` in kap_parser.py
- All 3 FOND-01 TDD tests pass (green); full suite: 3 passed, 6 xfailed

## Task Commits

Each task was committed atomically:

1. **Task 1: FOND-03 — Remove unused ML dependencies** - `bce392a` (chore)
2. **Task 2 TDD RED: FOND-01 failing tests** - `7f4aa3d` (test)
3. **Task 2 TDD GREEN: FOND-01 implementation** - `065d1ab` (feat)

_Note: TDD task split into RED + GREEN commits per TDD protocol_

## Files Created/Modified
- `backend/requirements.txt` — removed 4 unused ML packages; feedparser==6.0.11 retained
- `backend/app/services/kap_parser.py` — hard feedparser import, mock method deleted, all 3 fallback paths removed, datetime.utcnow() fixed
- `backend/app/main.py` — feedparser RuntimeError guard added in lifespan()
- `backend/tests/test_kap_parser.py` — 3 FOND-01 tests (no xfail markers, all green)

## Decisions Made
- vaderSentiment confirmed independent of torch/transformers — not added to requirements.txt since it's already installed in venv
- datetime.utcnow() in `get_recent_feed` and `get_recent_scenarios` methods also fixed (deviation Rule 1 — same file, already open)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed datetime.utcnow() in get_recent_feed and get_recent_scenarios**
- **Found during:** Task 2 (kap_parser.py editing)
- **Issue:** Plan specified fixing lines 200 and 290, but `get_recent_feed` (line 265) and `get_recent_scenarios` (lines 305, 355, 381) also used `datetime.utcnow()` in isoformat() fallbacks
- **Fix:** Replaced all 4 remaining `datetime.utcnow()` occurrences with `datetime.now(timezone.utc)` using replace_all edit
- **Files modified:** backend/app/services/kap_parser.py
- **Verification:** `grep "datetime.utcnow()" backend/app/services/kap_parser.py` returns nothing
- **Committed in:** 065d1ab (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug — extra utcnow occurrences in same file)
**Impact on plan:** Strictly in scope — same file already open, all occurrences fixed for consistency with FOND-05 intent.

## Issues Encountered
- pytest not pre-installed in venv — installed pytest==8.4.2 and pytest-asyncio==1.2.0 via pip during TDD RED phase
- A file watcher reverted test_kap_parser.py to xfail version during Task 2; re-written immediately

## Known Stubs
None — no stub values were introduced. Empty list returns are correct failure semantics, not stubs.

## Next Phase Readiness
- FOND-01 and FOND-03 complete — data integrity (no mock KAP data) and clean dependencies established
- FOND-02 (scoring weights) is next — scoring.py BASE_WEIGHTS must be replaced with settings reads
- FOND-04 (router split) and FOND-05 (UTC timestamps) follow

## Self-Check: PASSED
- backend/requirements.txt: tensorflow/torch/transformers/sentencepiece absent — CONFIRMED
- backend/app/services/kap_parser.py: _generate_mock_announcements absent, feedparser hard-imported — CONFIRMED
- backend/app/main.py: RuntimeError guard with feedparser present — CONFIRMED
- backend/tests/test_kap_parser.py: 3 tests pass (not xfail) — CONFIRMED
- Commits bce392a, 7f4aa3d, 065d1ab all exist in git log — CONFIRMED

---
*Phase: 01-foundation-repair*
*Completed: 2026-04-17*
