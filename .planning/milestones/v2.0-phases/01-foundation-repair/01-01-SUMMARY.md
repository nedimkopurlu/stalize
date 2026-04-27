---
phase: 01-foundation-repair
plan: "01"
subsystem: backend/tests
tags: [testing, pytest, tdd, red-phase, foundation]
dependency_graph:
  requires: []
  provides: [backend/pytest.ini, backend/tests/conftest.py, backend/tests/test_kap_parser.py, backend/tests/test_scoring.py, backend/tests/test_routers.py, backend/tests/test_models.py]
  affects: [01-02, 01-03, 01-04, 01-05]
tech_stack:
  added: [pytest-8.4.2, pytest-asyncio-1.2.0]
  patterns: [xfail stubs, MagicMock fixtures, monkeypatching]
key_files:
  created:
    - backend/pytest.ini
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_kap_parser.py
    - backend/tests/test_scoring.py
    - backend/tests/test_routers.py
    - backend/tests/test_models.py
  modified: []
decisions:
  - "Used strict=False on xfail to allow early xpass without breaking suite"
  - "mock_stock deletes macro_score attribute via del to force AttributeError on access"
metrics:
  duration_minutes: 2
  completed_date: "2026-04-17"
  tasks_completed: 3
  tasks_total: 3
  files_created: 7
  files_modified: 0
---

# Phase 01 Plan 01: Pytest Test Infrastructure (RED Phase) Summary

**One-liner:** pytest 8.4.2 infrastructure with asyncio_mode=auto and 9 xfail stubs covering FOND-01/02/04/05 verification contracts.

## Objective

Create test infrastructure for Phase 1 so all subsequent implementation tasks have automated verification available. Tests are RED phase stubs — marked xfail intentionally, designed to flip green as Waves 1-3 implement fixes.

## What Was Built

### pytest.ini
Configured with `asyncio_mode = auto` (required for pytest-asyncio), `testpaths = tests`, standard `python_files/classes/functions` patterns.

### tests/conftest.py
Two shared fixtures:
- `mock_settings`: MagicMock with all WEIGHT_* values matching config.py defaults (TECHNICAL=0.20, FUNDAMENTAL=0.25, ML=0.20, SENTIMENT=0.10, CAUSAL=0.15, MACRO=0.10)
- `mock_stock`: MagicMock with all scoring fields at neutral values; `macro_score` deliberately deleted to test `getattr` fallback behavior
- `mock_stock_with_macro`: Extension of mock_stock with macro_score=48.0

### Test Stubs (9 total, all xfail with strict=False)

| File | Count | Requirement | Tests |
|------|-------|-------------|-------|
| test_kap_parser.py | 3 | FOND-01 | test_no_mock_method, test_startup_error_without_feedparser, test_kap_unreachable_returns_empty |
| test_scoring.py | 3 | FOND-02 | test_weights_from_settings, test_weight_change_propagates, test_missing_macro_score_neutral |
| test_routers.py | 2 | FOND-04 | test_endpoints_py_deleted, test_all_routes_registered |
| test_models.py | 1 | FOND-05 | test_model_portfolio_timezone |

## Verification Results

```
collected 9 items
8 xfailed, 1 xpassed, 1 warning in 0.49s
```

Suite exits green. `test_startup_error_without_feedparser` xpassed (behavior was already partially correct — feedparser is installed so the monkeypatch triggers as expected). All others xfail as designed.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create pytest infrastructure | 7db8cfb | backend/pytest.ini, backend/tests/__init__.py |
| 2 | Write conftest.py with shared fixtures | 8b46d19 | backend/tests/conftest.py |
| 3 | Write 4 test stub files (RED phase) | a9e74ad | test_kap_parser.py, test_scoring.py, test_routers.py, test_models.py |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

All test functions in this plan ARE intentional stubs (xfail by design). They will be resolved by implementation plans 01-02 through 01-05. No unintentional stubs exist.

## Self-Check

- [x] backend/pytest.ini exists with asyncio_mode = auto
- [x] backend/tests/__init__.py exists
- [x] backend/tests/conftest.py exists with mock_settings and mock_stock
- [x] backend/tests/test_kap_parser.py: 3 test functions
- [x] backend/tests/test_scoring.py: 3 test functions
- [x] backend/tests/test_routers.py: 2 test functions
- [x] backend/tests/test_models.py: 1 test function
- [x] All 3 task commits exist: 7db8cfb, 8b46d19, a9e74ad
- [x] Suite collects 9 tests and exits 0
