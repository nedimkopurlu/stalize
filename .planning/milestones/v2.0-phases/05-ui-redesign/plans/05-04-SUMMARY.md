---
phase: 05-ui-redesign
plan: 05-04
subsystem: frontend/stock-detail
tags: [candlestick, lightweight-charts, score-panel, ui]
requirements: [UIUX-02]

dependency_graph:
  requires: [05-01]
  provides: [stock-detail-candlestick-chart, score-layer-panel, teknik-ozet]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx]

tech_stack:
  added: []
  patterns:
    - lightweight-charts v5 addSeries(CandlestickSeries) API (not deprecated addCandlestickSeries)
    - ResizeObserver for responsive chart width, chart.remove() in useEffect cleanup
    - ScoreRing with showLabel + label props for inline labeled rings

key_files:
  created:
    - frontend/src/components/CandlestickPanel.tsx
    - frontend/src/components/ScoreLayerPanel.tsx
  modified:
    - frontend/src/app/stocks/[symbol]/page.tsx

decisions:
  - Used ResizeObserver (not window resize event) for responsive chart width — cleaner cleanup
  - Removed SMA legend from chart tab since candlestick chart does not render SMA overlays
  - ScoreRing already supports label + showLabel props — no workaround needed
  - Kept ScoreLayerPanel props as `stock: StockSummary` (not individual score fields) for simpler integration

metrics:
  duration_minutes: 18
  completed_date: "2026-04-18"
  tasks_completed: 2
  files_changed: 3
---

# Phase 05 Plan 04: Stock Detail — Candlestick Chart + 3-Layer Scores Summary

Stock detail page now renders a lightweight-charts v5 candlestick chart (green/red candles) with ResizeObserver cleanup, a unified ScoreLayerPanel showing Genel/Temel/Teknik/Algi rings in one row, and a Teknik Özet section with the top 3 technical signals.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create CandlestickPanel.tsx and ScoreLayerPanel.tsx | 71ed302a | CandlestickPanel.tsx, ScoreLayerPanel.tsx |
| 2 | Replace canvas chart and score grid in stock detail page | a58a9d25 | stocks/[symbol]/page.tsx |

## Decisions Made

1. **lightweight-charts v5 API:** Used `chart.addSeries(CandlestickSeries, options)` — the v4 `addCandlestickSeries()` no longer exists in v5 and would throw at runtime.

2. **ResizeObserver over window.resize:** Used `new ResizeObserver()` on the container element rather than `window.addEventListener('resize')`. This avoids global listener leaks and responds to container-level size changes (e.g., sidebar toggle) not just window resizes.

3. **ScoreLayerPanel receives full `stock: StockSummary`** rather than individual score fields. Reduces prop drilling and keeps the component aligned with how the page already has `detail.stock` available.

4. **Removed SMA legend:** The original canvas chart drew SMA50/SMA200 overlay lines, which had a legend. The candlestick chart does not currently overlay SMAs (the `PricePoint` type includes `sma_50`/`sma_200` fields but they are not rendered as series). The legend was removed to avoid confusion. A future plan can add SMA line series if desired.

5. **ScoreRing label prop:** ScoreRing already supports `label` and `showLabel` props natively — no workaround was needed.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is wired from real API calls (`api.getStockPrices`, `api.getStockDetail`, `api.getStockTechnical`).

## Self-Check: PASSED

- frontend/src/components/CandlestickPanel.tsx: FOUND
- frontend/src/components/ScoreLayerPanel.tsx: FOUND
- Commit 71ed302a: FOUND (git log confirms)
- Commit a58a9d25: FOUND (git log confirms)
- `npm run build` exits 0: CONFIRMED
- `addCandlestickSeries` not in runtime code (only in comment): CONFIRMED
- `ScoreLayerPanel` and `CandlestickPanel` both imported and used in page.tsx: CONFIRMED
