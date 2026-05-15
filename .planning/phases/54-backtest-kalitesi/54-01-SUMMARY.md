---
phase: 54
plan: "01"
subsystem: backend/signal-tracking
tags: [backtest, slippage, regime, calibration, signal-tracking]
dependency_graph:
  requires: [market_regime table (Phase 50), Stock.liquidity_score (Phase 49), signal_tracking.py]
  provides: [calculate_round_trip_cost, _fetch_regime_map, by_regime calibration breakdown, by_slippage_cost summary, regime filter on /signals/outcomes and /signals/calibration]
  affects: [backend/app/services/signal_tracking.py, backend/app/api/signals.py]
tech_stack:
  added: []
  patterns: [SQLAlchemy async select with .in_(), module-level pure function alongside service class, TDD RED→GREEN cycle]
key_files:
  created: [backend/tests/test_backtest_cost_regime.py]
  modified: [backend/app/services/signal_tracking.py, backend/app/api/signals.py]
decisions:
  - _slippage_cost_summary uses assumed 0.6% round-trip cost (orta tier) because SignalDecisionSnapshot does not store is_bist30/liquidity_score at snapshot time
  - _fetch_regime_map wraps query in try/except to degrade gracefully if market_regime table is empty or unavailable
  - _serialize_with_regime added as a thin wrapper over _serialize to avoid breaking existing callers of _serialize
metrics:
  duration_seconds: 176
  completed_date: "2026-05-15"
  tasks_completed: 2
  files_modified: 3
---

# Phase 54 Plan 01: Backtest Kalitesi — Slippage + Regime Tagging Summary

Regime-aware signal calibration with realistic round-trip cost model: `calculate_round_trip_cost`, `_fetch_regime_map`, `by_regime` breakdown, and `by_slippage_cost` summary added to the signal tracking service. Both `/signals/outcomes` and `/signals/calibration` endpoints now accept an optional `regime` query parameter.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 (RED) | Failing tests for calculate_round_trip_cost | 62a08c3 | backend/tests/test_backtest_cost_regime.py |
| 1 (GREEN) | calculate_round_trip_cost + _fetch_regime_map | c6224f1 | backend/app/services/signal_tracking.py |
| 2 | calibration_report + list_outcomes + endpoint params | b697457 | backend/app/services/signal_tracking.py, backend/app/api/signals.py |

## New Functions and Methods

### Module-level (signal_tracking.py)

**`calculate_round_trip_cost(is_bist30: bool, liquidity_score: Optional[str]) -> float`**
Returns the full round-trip transaction cost as a decimal fraction.

| Condition | Slippage | Commission (each way) | Round-trip total |
|-----------|----------|----------------------|-----------------|
| is_bist30=True or "yüksek" | 10 bps | 10 bps | 0.004 (0.4%) |
| "orta" or None (default) | 20 bps | 10 bps | 0.006 (0.6%) |
| "düşük" | 40 bps | 10 bps | 0.010 (1.0%) |
| is_bist30=True overrides "düşük" | 10 bps | 10 bps | 0.004 |

### SignalTrackingService methods added

**`async _fetch_regime_map(db, dates) -> dict`**
Queries `market_regime` table for the given date list. Returns `{date: regime_string}`. Returns empty dict gracefully if table is empty.

**`_bucket_rows_by_regime(rows, regime_map, horizon) -> list[dict]`**
Groups signal rows by market regime label, returns one `_calibration_bucket` per regime.

**`_slippage_cost_summary(rows, horizon) -> dict`**
Computes gross vs net average return assuming 0.6% round-trip cost (orta tier). Returns: `assumed_round_trip_cost_pct`, `gross_avg_return_pct`, `net_avg_return_pct`, `note`.

**`_serialize_with_regime(row, regime_map) -> dict`**
Wraps `_serialize()` and appends `"regime"` field. Used by `list_outcomes`.

### Updated method signatures

- `list_outcomes(db, limit, action, outcome, horizon, regime=None)` — new `regime` kwarg; items now include `"regime"` field; regime filter applied before serialization
- `calibration_report(db, horizon, min_count, regime=None)` — new `regime` kwarg; response includes `"by_regime"` and `"by_slippage_cost"` keys

## API Changes

### GET /signals/outcomes
New query param: `regime: Optional[str]` — filters to signals on dates matching the given regime label (Boğa/Ayı/Yatay/Volatil). Each item in response now includes `"regime"` field.

### GET /signals/calibration
New query param: `regime: Optional[str]` — filters signals to the given regime before computing all bucket metrics.
Response now includes:
- `"by_regime"`: list of calibration buckets (one per detected regime)
- `"by_slippage_cost"`: `{assumed_round_trip_cost_pct, gross_avg_return_pct, net_avg_return_pct, note}`

## Test Results

```
backend/tests/test_backtest_cost_regime.py — 6 passed
```

Tests cover: BIST30=True, orta, düşük, yüksek, None (default), and is_bist30 overrides düşük.

## Deviations from Plan

None — plan executed exactly as written. The `assumed_cost_pct` value in `_slippage_cost_summary` is 0.6 (matching `0.6%` described in plan action item 4). The `_serialize_with_regime` helper was introduced to keep `_serialize` unchanged (backward-compatible), which is a minor structural improvement within plan scope.

## Known Stubs

None — all new fields are computed from actual data (regime_map from DB, return fields from snapshot). The `_slippage_cost_summary` uses a stated assumption (orta tier default) which is documented in the response `note` field and in this summary.

## Self-Check: PASSED

Files exist:
- backend/app/services/signal_tracking.py — FOUND
- backend/app/api/signals.py — FOUND
- backend/tests/test_backtest_cost_regime.py — FOUND

Commits exist: 62a08c3, c6224f1, b697457 — all present in git log.
