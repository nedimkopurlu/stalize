---
phase: 01-foundation-repair
plan: "03"
subsystem: backend/scoring
tags: [scoring, config, weights, settings, tdd, green-phase, FOND-02]
dependency_graph:
  requires: [01-01]
  provides: [backend/app/services/scoring.py (settings-driven weights)]
  affects: [01-04, 01-05]
tech_stack:
  added: []
  patterns: [pydantic-settings runtime read, getattr safe fallback, settings singleton]
key_files:
  created: []
  modified:
    - backend/app/services/scoring.py
decisions:
  - "BASE_WEIGHTS class constant removed entirely — config.py is single source of truth (D-06)"
  - "macro_score uses getattr fallback — column does not exist on Stock model in this phase (D-05)"
  - "Crisis mode dict includes macro_score: 0.0 key to maintain consistent 6-key interface"
metrics:
  duration_minutes: 5
  completed_date: "2026-04-17"
  tasks_completed: 1
  tasks_total: 1
  files_created: 0
  files_modified: 1
---

# Phase 01 Plan 03: Settings-Driven Scoring Weights (GREEN Phase) Summary

**One-liner:** BASE_WEIGHTS class constant deleted; ScoringEngine._resolve_weights reads WEIGHT_* from pydantic-settings singleton at runtime, with getattr fallback for absent macro_score column.

## Objective

Replace the hardcoded BASE_WEIGHTS class constant in scoring.py with settings-driven weight reads. This makes config.py the single source of truth for all scoring weights — previously scoring.py used technical=0.30 while config.py said 0.20, silently corrupting every overall_score computation.

## What Was Built

### backend/app/services/scoring.py

Three targeted changes:

**1. Settings import added:**
```python
from app.core.config import settings
```

**2. BASE_WEIGHTS class constant deleted entirely** (was using stale wrong values: technical=0.30, not the config-correct 0.20).

**3. _resolve_weights rewritten** to read from settings singleton:
- Normal mode: returns dict with 6 keys reading from `settings.WEIGHT_TECHNICAL` etc.
- Crisis mode: returns hardcoded crisis weights dict with 6 keys (including `"macro_score": 0.0`)
- No intermediate variable holding the old BASE_WEIGHTS dict

**4. calculate_overall_score updated** to include macro_score in scores dict:
```python
"macro_score": getattr(stock, "macro_score", None),  # column absent in this phase — safe fallback
```

The existing `weighted_sum / total_weight` normalization already handles None values correctly — no changes to that logic.

## Verification Results

```
collected 3 items (test_scoring.py)
3 xpassed, 1 warning
```

All 3 FOND-02 tests now XPASS (were xfail before this plan):
- `test_weights_from_settings`: ScoringEngine has no BASE_WEIGHTS attribute
- `test_weight_change_propagates`: patching settings.WEIGHT_TECHNICAL=0.99 propagates correctly
- `test_missing_macro_score_neutral`: missing macro_score column does not raise AttributeError

Full suite: 3 passed, 2 xfailed, 4 xpassed — all green.

Weight sum check: `settings.WEIGHT_TECHNICAL + ... + settings.WEIGHT_MACRO = 1.00`

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | FOND-02: Replace BASE_WEIGHTS with settings-driven weights | da10cac | backend/app/services/scoring.py |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. scoring.py is fully wired to settings; macro_score uses intentional getattr fallback (documented: column does not exist in this phase — will be added in a future migration).

## Self-Check

- [x] `grep "BASE_WEIGHTS" backend/app/services/scoring.py` returns nothing (exit 1)
- [x] `grep "settings.WEIGHT_TECHNICAL" backend/app/services/scoring.py` returns a match
- [x] `grep "getattr.*macro_score" backend/app/services/scoring.py` returns a match
- [x] `grep '"macro_score": 0.0' backend/app/services/scoring.py` returns a match in crisis mode dict
- [x] `grep -c "settings.WEIGHT_" scoring.py` returns 6
- [x] `python3 -m pytest tests/test_scoring.py -v` — 3 xpassed
- [x] `python3 -m pytest tests/ -v` — 3 passed, 2 xfailed, 4 xpassed
- [x] Weight sum = 1.00
- [x] Task commit exists: da10cac

## Self-Check: PASSED
