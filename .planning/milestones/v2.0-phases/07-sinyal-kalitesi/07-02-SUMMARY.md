---
phase: 07-sinyal-kalitesi
plan: "02"
subsystem: backend/technical-analysis
tags: [sgnl-01, sgnl-03, stop-loss, target-price, rsi-divergence, tdd]
dependency_graph:
  requires: [07-01]
  provides: [_compute_stop_loss, _compute_target_price, _detect_rsi_divergence, analyze_stock.stop_loss, analyze_stock.target_price]
  affects: [backend/app/api/stocks.py GET /stocks/{symbol}/technical]
tech_stack:
  added: []
  patterns: [scipy.signal.find_peaks for divergence detection, last-point-as-extremum for trending series]
key_files:
  created: []
  modified:
    - backend/app/services/technical.py
    - backend/tests/test_signal_quality.py
decisions:
  - "Extended _detect_rsi_divergence to compare last data point vs most recent formal peak/dip — scipy find_peaks cannot identify endpoint-of-series as a local extremum in monotonically trending data"
  - "Divergence is additive to signals[] list — no existing signal removed or modified"
  - "last_close added to indicators sub-dict to support endpoint assertion in test_technical_endpoint_includes_stop_loss_and_target"
metrics:
  duration_minutes: 4
  completed_date: "2026-04-19"
  tasks_completed: 1
  files_modified: 2
requirements: [SGNL-01, SGNL-03]
---

# Phase 07 Plan 02: ATR Stop-Loss, Target Price, RSI Divergence — Summary

**One-liner:** ATR-based stop-loss (`close - 2*ATR14`), first-resistance target price (max swing high or +5% fallback), and RSI-price divergence detection wired into TechnicalAnalysisEngine.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement ATR stop-loss, target price, RSI divergence + wire into analyze_stock | 4ae9f19c | backend/app/services/technical.py, backend/tests/test_signal_quality.py |

## What Was Built

Three new private methods added to `TechnicalAnalysisEngine` in `backend/app/services/technical.py`:

1. **`_compute_stop_loss(df)`** — Returns `round(last_close - 2 * atr_14, 2)`. Returns `None` if either value is NaN. Satisfies SGNL-01.

2. **`_compute_target_price(df)`** — Scans `df["high"].tail(20)` for the max value strictly above `last_close`. Falls back to `round(last_close * 1.05, 2)` when none exists. Satisfies SGNL-01.

3. **`_detect_rsi_divergence(df)`** — Detects RSI-price divergence in the last 20 bars:
   - Bullish: price lower-low, RSI higher-low
   - Bearish: price higher-high, RSI lower-high
   - Returns `None` when no divergence present
   Satisfies SGNL-03.

`analyze_stock()` return dict extended with `stop_loss`, `target_price` (top-level) and `last_close` inside `indicators`. `detect_signals()` now appends divergence signals additively.

## Test Results

- SGNL-01 tests: 4/4 GREEN
- SGNL-03 tests: 3/3 GREEN
- SGNL-02 tests: 3/4 GREEN (unit helpers from plan 07-03 parallel commit), 1 RED (endpoint — plan 07-03 owns it)
- No regressions in other test suites (35 passed, 13 xpassed)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted RSI divergence algorithm for trending series endpoints**

- **Found during:** Task 1 verification
- **Issue:** `scipy.signal.find_peaks` cannot identify the last point in a monotonically trending series as a local minimum/maximum, because a local peak requires the adjacent value to be lower. The test data `closes = [100, 98, 96, 94, 92, 94, 93, 91, 90, 89]` produces only one formal dip (index 4, value 92), leaving no second dip for comparison.
- **Fix:** Extended the algorithm to also compare the most recent formal dip/peak against the last data point (treated as the current extremum position) when there is only one formal extremum. Two comparison pairs are evaluated: (dip[-2], dip[-1]) and (dip[-1], last_idx).
- **Files modified:** backend/app/services/technical.py
- **Commit:** 4ae9f19c

## Known Stubs

None — stop_loss and target_price flow from real ATR/price data in analyze_stock.

## Self-Check: PASSED

- [x] `backend/app/services/technical.py` modified — exists
- [x] Commit 4ae9f19c — confirmed in git log
- [x] `_compute_stop_loss`, `_compute_target_price`, `_detect_rsi_divergence` each appear exactly 2 times (definition + call)
- [x] 7 SGNL-01/03 tests GREEN
- [x] SGNL-02 endpoint test still RED (pytest.fail guard)
- [x] No regression in other test files
