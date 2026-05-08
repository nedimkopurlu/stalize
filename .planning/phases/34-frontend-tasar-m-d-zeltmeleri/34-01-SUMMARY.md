---
phase: 34-frontend-tasar-m-d-zeltmeleri
plan: "01"
subsystem: frontend/dashboard
tags: [design, dashboard, chart, sparkline, typescript]
dependency_graph:
  requires: []
  provides: [DESIGN-01, DESIGN-02]
  affects: [frontend/src/app/page.tsx, frontend/src/app/page.module.css]
tech_stack:
  added: []
  patterns:
    - LCG-based deterministic mock data series (seedSeries helper)
    - Inline SVG mini sparkline sub-component (MiniSparkline)
    - Optional prop extension on existing chart component (seedValues)
key_files:
  created: []
  modified:
    - frontend/src/app/page.tsx
    - frontend/src/app/page.module.css
decisions:
  - seedSeries uses LCG (linear congruential generator) for determinism — same seed always produces same array, no Math.random()
  - MiniSparkline is a module-local sub-component, not exported — keeps it co-located with its only consumer (StockRows)
  - Base value for BIST100 mock chart falls back to 9000 when bist100 data not yet loaded — avoids flicker
  - Spread for stock sparklines is max(2, price*0.04) to scale correctly across low-price and high-price stocks
metrics:
  duration: "~2 minutes"
  completed: "2026-05-08T05:05:34Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 34 Plan 01: Dashboard Chart Period Tabs + Stock Row Sparklines Summary

**One-liner:** Added 6-tab BIST100 period selector with LCG mock data for 1G/1H, plus 40x28px inline SVG sparklines in stock rows — both confined to page.tsx and page.module.css.

## What Was Built

### Task 1 — BIST100 Chart: 6 Period Tabs with 1G/1H Mock Data (commit: ae5b666)

- `seedSeries(seed, n, base, spread)`: Deterministic LCG helper. Same seed string always produces same number array. Used for both chart periods and stock sparklines.
- `Bist100Chart` extended with optional `seedValues?: number[]` prop. When period is `'1G'` or `'1H'` and seedValues is provided, the chart renders seed data instead of real history points.
- `chartPeriod` state type extended: `'1G' | '1H' | '1A' | '3A' | '1Y' | 'Tüm'` (was `'1A' | '3A' | '1Y' | 'Tüm'`).
- Period tabs array updated: `['1G', '1H', '1A', '3A', '1Y', 'Tüm'] as const` — 6 buttons in specified order.
- Chart JSX conditional: 1G → 48-point seedSeries; 1H → 30-point seedSeries; other periods → real `bistHistory.points`; no data → skeleton div.

### Task 2 — StockRows: 40x28px MiniSparkline (commit: ea9742e)

- `MiniSparkline({ values, up })`: Inline SVG sub-component. Renders a 40x28px polyline chart. Stroke uses `var(--accent-green)` when `up=true`, `var(--accent-red)` when false.
- `StockRows` updated: each row now generates `sparkValues = seedSeries(symbol, 20, price, max(2, price*0.04))` and renders `<MiniSparkline>` between `stockName` and `stockPrice`.
- `.stockRow` CSS grid changed from `52px 1fr 68px 68px` to `52px 1fr 40px 68px 68px` (5 columns, new 40px sparkline slot).

## Verification

```
cd frontend && npx tsc --noEmit
# Exit 0, no output — zero errors
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All sparklines use deterministic seedSeries data. The 1G/1H chart uses mock data intentionally (no intraday backend data exists); this is by design per the plan spec.

## Self-Check: PASSED

- [x] `frontend/src/app/page.tsx` modified and committed (ae5b666, ea9742e)
- [x] `frontend/src/app/page.module.css` modified and committed (ea9742e)
- [x] `grep -n "function seedSeries"` → 1 match at line 24
- [x] `grep -n "'1G' | '1H' | '1A' | '3A' | '1Y' | 'Tüm'"` → 1 match at line 120
- [x] `grep -n "function MiniSparkline"` → 1 match at line 360
- [x] `grep -n "52px 1fr 40px 68px 68px"` → 1 match in page.module.css
- [x] `npx tsc --noEmit` → exit 0
