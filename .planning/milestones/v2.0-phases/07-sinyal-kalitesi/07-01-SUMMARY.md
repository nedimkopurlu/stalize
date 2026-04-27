---
phase: 07-sinyal-kalitesi
plan: 01
subsystem: testing
tags: [pytest, tdd, signal-quality, atr, volume-ratio, rsi-divergence]

# Dependency graph
requires:
  - phase: 06-teknik-duzeltmeler
    provides: clean async foundation, correct ML scoring without double-count
provides:
  - 11 RED test stubs encoding exact contract for SGNL-01, SGNL-02, SGNL-03
  - Failure-guaranteed guards that only turn GREEN after 07-02/07-03 implementation
affects: [07-02-sinyal-impl, 07-03-sinyal-impl]

# Tech tracking
tech-stack:
  added: []
  patterns: [pytest.fail("RED — ...") guard ensures tests cannot pass accidentally before implementation]

key-files:
  created:
    - backend/tests/test_signal_quality.py
  modified: []

key-decisions:
  - "Plain pytest.fail() RED guards placed before assertions — same pattern as Phase 2/6 TDD stubs"
  - "SGNL-02 import (compute_volume_ratio) inside test body to avoid collection break before function exists"
  - "Async tests use @pytest.mark.asyncio matching existing conftest pattern"

patterns-established:
  - "RED stubs: pytest.fail() as first line guarantees no accidental pass even if implementation partially exists"
  - "_synthetic_df() helper builds minimal DataFrame with all columns technical engine expects"

requirements-completed: [SGNL-01, SGNL-02, SGNL-03]

# Metrics
duration: 8min
completed: 2026-04-19
---

# Phase 07 Plan 01: Sinyal Kalitesi RED Stubs Summary

**11 pytest RED stubs encoding ATR stop-loss formula, volume ratio normalization, and RSI divergence detection contracts for SGNL-01/02/03**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-19T09:11:49Z
- **Completed:** 2026-04-19T09:19:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `backend/tests/test_signal_quality.py` with 11 failing RED test stubs
- All 11 tests verified to fail immediately via `pytest.fail("RED — ...")` guard
- Test collection clean: no import errors, no accidental passes
- Covers all three requirements: SGNL-01 (4 tests), SGNL-02 (4 tests), SGNL-03 (3 tests)

## Task Commits

1. **Task 1: Write failing tests for SGNL-01, SGNL-02, SGNL-03** - `215ec72a` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/tests/test_signal_quality.py` - 11 RED pytest stubs for signal quality contracts: ATR stop-loss/target price (SGNL-01), volume ratio normalization (SGNL-02), RSI bullish/bearish/no-divergence detection (SGNL-03)

## Decisions Made

- Plain `pytest.fail("RED — ...")` guard before every assertion — same pattern established in Phase 2/6, prevents accidental passes
- `from app.services.technical import compute_volume_ratio` placed inside test body (after `pytest.fail`) so collection does not break before the function exists in 07-02
- `_synthetic_df()` helper constructs minimal DataFrame with `close`, `high`, `low`, `volume`, `rsi_14`, `atr_14` columns matching what `TechnicalAnalysisEngine` expects

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 11 RED tests are in place and fail loudly
- Plans 07-02 and 07-03 can now drive implementations against an explicit contract
- No blockers — test infrastructure (conftest.py, pytest-asyncio) already present from prior phases

---
*Phase: 07-sinyal-kalitesi*
*Completed: 2026-04-19*
