---
phase: 14-hisse-detay-yeniden-tasarim
plan: "02"
subsystem: frontend-charts + backend-technical
tags: [lightweight-charts, ema, candlestick, rsi, volume, technical-analysis, vizz-01]
dependency_graph:
  requires: [14-01]
  provides: [CandlestickEMAPanel, ema_50_series, ema_200_series]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx, backend/app/services/technical.py]
tech_stack:
  added: []
  patterns:
    - lightweight-charts v5 addSeries(SeriesType, options) pattern
    - _build_ema_series() inner function for DataFrame-to-list conversion
    - Multi-panel chart: candlestick + volume + RSI on shared time axis with separate price scales
key_files:
  created:
    - frontend/src/components/CandlestickEMAPanel.tsx
  modified:
    - backend/app/services/technical.py
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/[symbol]/page.tsx
decisions:
  - "lineWidth set to integer 2 for RSI series (lightweight-charts v5 LineWidth type does not accept 1.5)"
  - "_build_ema_series implemented as inner function inside analyze_stock() to access df closure without instance method overhead"
  - "EMA series attached to same price scale as candlestick via scaleMargins matching (top:0.05, bottom:0.40)"
metrics:
  duration_seconds: 170
  completed_date: "2026-04-26"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
requirements: [VIZZ-01]
---

# Phase 14 Plan 02: EMA Overlay + Volume + RSI Chart Panel Summary

Backend technical endpoint now exposes ema_50[] and ema_200[] date-value series; frontend CandlestickEMAPanel renders candlestick with orange EMA50/blue EMA200 overlays, a volume histogram with above-average highlighting, and a RSI panel with 70/30 reference lines — all using lightweight-charts v5 on the stock detail page.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Backend: ema_200 to calculate_indicators + _build_ema_series + ema_50/ema_200 in analyze_stock return | 20eb25cf | backend/app/services/technical.py |
| 2 | Frontend: api.ts TechnicalResult update + CandlestickEMAPanel + page.tsx integration | b886c61b | frontend/src/lib/api.ts, frontend/src/components/CandlestickEMAPanel.tsx, frontend/src/app/stocks/[symbol]/page.tsx |

## What Was Built

**Backend (technical.py):**
- `df["ema_200"] = ta.trend.ema_indicator(close, window=200)` added to `calculate_indicators()`
- `_build_ema_series(column: str)` inner function in `analyze_stock()` converts DataFrame EMA columns to `[{date, value}]` lists, dropping NaN rows
- `"ema_50"` and `"ema_200"` keys added to the `analyze_stock()` return dict; empty list `[]` returned when insufficient data (< 200 bars for EMA200)

**Frontend (CandlestickEMAPanel.tsx):**
- Candlestick series with green/red wicks, price scale margins `top:0.05 / bottom:0.40`
- EMA 50 line series in orange (#f97316), same price scale as candlestick
- EMA 200 line series in blue (#3b82f6), same price scale as candlestick
- Volume histogram series (priceScaleId: 'volume'), margins `top:0.72 / bottom:0.14`; bars above average volume rendered at 80% opacity, others at 35%
- RSI line series in purple (#a855f7) (priceScaleId: 'rsi'), margins `top:0.84 / bottom:0.0`; horizontal reference price lines at 70 (red dashed) and 30 (green dashed)
- ResizeObserver for responsive width; cleanup on unmount
- Empty state while `prices.length === 0`

**api.ts:** `ema_50?: Array<{date: string; value: number}>` and `ema_200?` added to `TechnicalResult` interface.

**page.tsx:** `CandlestickPanel` replaced with `CandlestickEMAPanel`; `ema50={technical?.ema_50 ?? []}` and `ema200={technical?.ema_200 ?? []}` props passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed lineWidth: 1.5 TypeScript error in CandlestickEMAPanel**
- **Found during:** Task 2 verification (tsc --noEmit)
- **Issue:** lightweight-charts v5 `LineWidth` type only accepts integer values (1, 2, 3, 4); `1.5` caused TS2322 type error
- **Fix:** Changed RSI `lineWidth: 1.5` to `lineWidth: 2`
- **Files modified:** frontend/src/components/CandlestickEMAPanel.tsx
- **Commit:** b886c61b (included in same commit)

## Pre-existing Issues (Out of Scope)

**Stale .next/dev/types/app/causal/page.ts artifact** — The causal page was deleted in a previous phase but `.next` build cache retains a stale type-check file referencing it. This causes 2 TS errors unrelated to Plan 14-02. Logged to deferred-items as pre-existing.

## Known Stubs

None — EMA data flows directly from backend `analyze_stock()` through `TechnicalResult.ema_50` / `ema_200` props. Volume and RSI data sourced from `PricePoint[]` prices array already fetched on the page.

## Self-Check: PASSED

All 4 files exist. Both task commits (20eb25cf, b886c61b) confirmed in git log.
