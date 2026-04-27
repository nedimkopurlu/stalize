---
phase: 06-teknik-duzeltmeler
plan: "03"
subsystem: backend-services
tags: [tech-debt, pandas, ml, scoring, tdd]
dependency_graph:
  requires: []
  provides: [TECH-03, TECH-04]
  affects: [dynamic_correlation, ml_scoring, overall_score]
tech_stack:
  added: []
  patterns: [tdd-red-green, source-structural-guard, positional-pandas-api]
key_files:
  created:
    - backend/tests/test_pandas_ffill.py
    - backend/tests/test_ml_no_double_count.py
  modified:
    - backend/app/services/dynamic_correlation.py
    - backend/app/services/ml.py
decisions:
  - "TECH-03: df.ffill() positional API replaces fillna(method='ffill') — single-line change, no logic change"
  - "TECH-04: _normalize_score drops causal_score param entirely; causal enters overall_score only via scoring.py WEIGHT_CAUSAL"
  - "Test structural guard uses async def boundary detection to scope function body extraction correctly"
metrics:
  duration_minutes: 20
  completed_date: "2026-04-19"
  tasks_completed: 3
  files_modified: 4
---

# Phase 06 Plan 03: TECH-03 and TECH-04 — pandas ffill + ML double-count fixes Summary

One-liner: Fixed deprecated `fillna(method='ffill')` → `ffill()` in dynamic_correlation.py (TECH-03) and removed `causal_score * 0.2` blend from `ml.py _normalize_score` (TECH-04) so causal enters overall_score exactly once via scoring.py's WEIGHT_CAUSAL.

## What Was Built

### TECH-03: pandas positional API migration

`dynamic_correlation.py` line 124 changed from:
```python
df_pivot = df_pivot.fillna(method="ffill").dropna()
```
to:
```python
df_pivot = df_pivot.ffill().dropna()
```

Eliminates pandas FutureWarning about deprecated `fillna(method=)` keyword argument. Single-line change with no logic impact.

### TECH-04: Remove causal double-count in ML scoring

`ml.py _normalize_score` updated:
- **Signature**: `_normalize_score(self, pred_return: float)` — `causal_score: float = 50.0` parameter removed
- **Body**: `base_score = 50.0 + (pred_return * 500); return max(0.0, min(100.0, base_score))` — `weighted_score = (base_score * 0.8) + (causal_score * 0.2)` blend removed
- **Caller** in `analyze_stock`: `c_score` local variable removed; call simplified to `self._normalize_score(pred_return or 0.0)`
- **Log line**: `Haber Etkisi: {c_score:.1f}` reference removed

`scoring.py` untouched — `causal_score: settings.WEIGHT_CAUSAL` remains the single legitimate entry point for causal into overall_score.

**Numeric impact**: Before TECH-04, causal_score effectively had weight ~0.35 (0.20 inside ml_score * 0.20 WEIGHT_ML + 0.15 WEIGHT_CAUSAL). After TECH-04, effective weight = exactly 0.15 (WEIGHT_CAUSAL only).

### Tests

**test_pandas_ffill.py** (2 tests — GREEN):
- `test_ffill_no_deprecation_warning`: Runtime check — no FutureWarning from forward-fill
- `test_source_has_no_fillna_method_kwarg`: Structural guard — source must not contain `fillna(method=`

**test_ml_no_double_count.py** (4 tests — GREEN):
- `test_normalize_score_signature_has_no_causal_param`: `inspect.signature` check
- `test_normalize_score_ignores_causal_via_source`: Source scoped to function body (async-def aware boundary detection)
- `test_normalize_score_returns_pure_base`: `pred_return=0 → 50.0`, `0.1 → 100.0`, `-0.1 → 0.0`
- `test_causal_counted_once_in_overall`: Integration — delta when causal goes 50→70 matches exactly `(20 * WEIGHT_CAUSAL) / total_weight`

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 (RED) | Add failing tests for TECH-03 and TECH-04 | 2fed9b80 |
| 2 (GREEN) | TECH-03: ffill() in dynamic_correlation.py | bd8381ca |
| 3 (GREEN) | TECH-04: remove causal blend from ml.py | 7637d351 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test source scan didn't account for async def method boundary**
- **Found during:** Task 3 GREEN phase
- **Issue:** `test_normalize_score_ignores_causal_via_source` used `"\n    def "` pattern to find the next class method after `_normalize_score`. Since `analyze_stock` is declared `async def`, the pattern didn't match, and the extracted "function body" extended through `analyze_stock` which contains `stock.causal_score` — causing a false FAIL.
- **Fix:** Updated test to find minimum of `"\n    def "` and `"\n    async def "` candidates, using the earliest boundary.
- **Files modified:** `backend/tests/test_ml_no_double_count.py`
- **Commit:** 7637d351

### Pre-existing Failures (Out of Scope)

`test_yfinance_async.py::test_macro_indicators_uses_executor` was failing before this plan (confirmed via git stash check). This is TECH-02 scope (async yfinance), not TECH-03/TECH-04. Deferred to plan 06-02.

## Test Results

- `test_pandas_ffill.py`: 2/2 PASSED
- `test_ml_no_double_count.py`: 4/4 PASSED
- `test_scoring.py`: 3/3 XPASSED (pre-existing xfail markers now pass)
- Full suite (excluding pre-existing `test_yfinance_async.py` failure): 30 passed, 13 xpassed, 0 failed

## Known Stubs

None — all changes are functional fixes with no placeholder values.

## Self-Check: PASSED

Files exist:
- backend/tests/test_pandas_ffill.py: FOUND
- backend/tests/test_ml_no_double_count.py: FOUND
- backend/app/services/dynamic_correlation.py: FOUND (modified)
- backend/app/services/ml.py: FOUND (modified)

Commits verified: 2fed9b80, bd8381ca, 7637d351 — all present in git log.
