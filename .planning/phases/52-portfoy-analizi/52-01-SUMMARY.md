---
phase: 52-portfoy-analizi
plan: "01"
subsystem: backend-api
tags: [portfolio, analytics, beta, correlation, position-sizing, atr, numpy]
dependency_graph:
  requires: []
  provides:
    - GET /portfolio/analytics
    - GET /stocks/{symbol}/position-size
  affects:
    - frontend/portfolio page (plan 52-02)
tech_stack:
  added: []
  patterns:
    - numpy cov/corrcoef for portfolio math
    - value-weighted portfolio return series
    - ATR-based position sizing from pre-computed DB column
key_files:
  created: []
  modified:
    - backend/app/api/portfolio_v2.py
    - backend/app/api/stocks.py
decisions:
  - "Beta formula: np.cov(port_returns, bench_returns)[0,1] / np.var(bench_returns, ddof=1), clamped to [0.0, 3.0]"
  - "Correlation uses 90-day window, minimum 20 data points per symbol; symbols below threshold go to excluded_symbols"
  - "ATR read from pre-computed PriceHistory.atr_14 column (latest row) — no runtime 14-day computation needed"
  - "position-size route placed before /decision wildcard to avoid FastAPI routing conflicts"
metrics:
  duration_minutes: 15
  completed_date: "2026-05-15"
  tasks_completed: 2
  files_modified: 2
---

# Phase 52 Plan 01: Portfolio Analytics Endpoints Summary

**One-liner:** Two new backend endpoints delivering beta vs BIST100 (252-day, numpy cov/var) and 90-day Pearson correlation matrix for active portfolio positions, plus ATR-based position sizing reading `atr_14` from the latest PriceHistory row.

## Endpoints Added

### GET /portfolio/analytics

**File:** `backend/app/api/portfolio_v2.py`

**Response shape:**
```json
{
  "beta": 0.8732,
  "correlation_matrix": {
    "symbols": ["THYAO", "GARAN"],
    "matrix": [[1.0, 0.45], [0.45, 1.0]],
    "excluded_symbols": []
  },
  "calculated_at": "2026-05-15T10:00:00+00:00",
  "position_count": 2
}
```

**When beta/correlation are null:** 0 active positions, or < 20 common data points with benchmark.

**Beta formula:**
```
cov(portfolio_returns, benchmark_returns) / var(benchmark_returns, ddof=1)
clipped to [0.0, 3.0]
```

**Benchmark:** XU100.IS via `_fetch_benchmark_history()` (CommodityPrice table → yfinance fallback).

**Weights:** Entry value-weighted (`entry_price * quantity / total_portfolio_value`).

### GET /stocks/{symbol}/position-size

**File:** `backend/app/api/stocks.py`

**Query param:** `portfolio_value: float = 100000.0`

**Response shape:**
```json
{
  "symbol": "THYAO",
  "current_price": 285.4,
  "atr_14": 7.2,
  "stop_distance": 14.4,
  "portfolio_value": 100000.0,
  "risk_amount_1pct": 1000.0,
  "risk_amount_2pct": 2000.0,
  "max_shares_1pct": 69,
  "max_shares_2pct": 138
}
```

**Stop distance:** `atr_14 * 2` (read from pre-computed `PriceHistory.atr_14`, latest row).

**Error cases:**
- 404 if stock not in DB or `is_active = False`
- 404 if no price history found
- `atr_14 = null` → `stop_distance = null`, `max_shares_*pct = null` (no division by zero)

## Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Beta window | 252 trading days | Standard 1-year lookback |
| Beta formula | cov / var(ddof=1) | Unbiased variance estimate |
| Beta clamp | [0.0, 3.0] | Prevents extreme outliers from noisy data |
| Correlation window | 90 days | Balance between recency and statistical validity |
| Min data points | 20 per symbol | Prevents meaningless correlation from sparse data |
| ATR source | PriceHistory.atr_14 column | Already pre-computed by technical engine; no extra math |
| Route order | position-size before decision | FastAPI matches `{symbol}/{sub}` routes in declaration order |

## Edge Cases Handled

- Empty portfolio: returns `{"beta": null, "correlation_matrix": null, "position_count": 0}`
- Symbol in portfolio but not in `stocks` table (inactive/deleted): skipped from computation
- Zero benchmark variance: beta not computed (avoids division by zero)
- NaN/Inf in returns: filtered via `np.isfinite()` mask before cov/var
- Single included symbol: correlation_matrix returns `[[1.0]]` (valid degenerate case)
- `atr_14 = null` in DB: `stop_distance = null`, shares = null (no crash)
- Symbol with `.IS` suffix in request: stripped via `.removesuffix(".IS")`

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- SUMMARY.md: FOUND
- Task 1 commit 25288a5: FOUND
- Task 2 commit 07cfac8: FOUND
