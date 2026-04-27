---
phase: 03-llm-infrastructure
plan: "03-00"
title: "Wave 0: xfail test stubs + validation scaffold"
subsystem: llm-infrastructure
tags: [testing, xfail, llm, scaffold]
dependency_graph:
  requires: []
  provides: [test-scaffold-llm-infrastructure]
  affects: [backend/tests/test_llm_infrastructure.py]
tech_stack:
  added: []
  patterns: [xfail-strict, test-driven-scaffold]
key_files:
  created:
    - backend/tests/test_llm_infrastructure.py
    - .planning/phases/03-llm-infrastructure/03-VALIDATION.md
  modified: []
decisions:
  - "strict=True on all xfail markers — prevents stubs from silently becoming no-ops when implementation lands"
metrics:
  duration_seconds: 64
  completed_date: "2026-04-17"
  tasks_completed: 2
  files_created: 2
---

# Phase 3 Plan 00: Wave 0 xfail test stubs + validation scaffold Summary

**One-liner:** 7 xfail strict stubs scaffolding LLMI-01 (StockAnalysis model + instructor + legacy adapter), LLMI-02 (semaphore), and LLMI-03 (staleness_warning) — all green at Wave 0.

## What Was Created

### Task 1: `backend/tests/test_llm_infrastructure.py`

7 xfail test stubs, all with `strict=True`:

| Test | Requirement |
|------|-------------|
| `test_stock_analysis_model_valid` | LLMI-01 |
| `test_stock_analysis_model_invalid_karar` | LLMI-01 |
| `test_semaphore_limits_concurrency` | LLMI-02 |
| `test_staleness_warning_set_when_old` | LLMI-03 |
| `test_no_staleness_warning_fresh` | LLMI-03 |
| `test_instructor_integration` | LLMI-01 |
| `test_legacy_dict_adapter` | LLMI-01 |

All 7 collected as xfail (exit code 0). No import errors, no collection errors.

### Task 2: `.planning/phases/03-llm-infrastructure/03-VALIDATION.md`

Validation strategy document containing:
- Quick run and full suite commands
- Requirement → test mapping table (LLMI-01/02/03)
- Phase gate condition (all 7 pass, non-xfail)
- Wave progress tracker
- Note on test_llm_cache.py migration needed in Wave 1

## Decisions Made

- `strict=True` on all xfail markers — if an implementation accidentally passes a test before the full feature lands, the suite will FAIL rather than silently accept it.

## Note on test_llm_cache.py (Wave 1 Migration Required)

After Wave 1 migrates `analyze()` to return `StockAnalysis` instead of a dict, the `make_mock_response` helper in `test_llm_cache.py` must be updated. The `_patched_client` (instructor-wrapped) is used for the API call, so mocks must return a `StockAnalysis` object, not an AsyncOpenAI response object.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `backend/tests/test_llm_infrastructure.py`: FOUND
- `.planning/phases/03-llm-infrastructure/03-VALIDATION.md`: FOUND
- Commit `e0e4c7e`: FOUND (test stubs)
- Commit `2508e29`: FOUND (VALIDATION.md)
