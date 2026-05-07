---
phase: 29-dashboard
plan: 01
subsystem: ui
tags: [react, nextjs, typescript, css-modules, market-data, bist100, forex, gold]

# Dependency graph
requires:
  - phase: 28-veri-altyap-s
    provides: /api/market/bist100, /api/market/forex, /api/market/gold endpoints with typed response shapes

provides:
  - MarketBist100Response, ForexPair, MarketForexResponse, MarketGoldResponse TypeScript interfaces in api.ts
  - getMarketBist100, getMarketForex, getMarketGold API client methods in api.ts
  - Phase 29 Dashboard page at / with BIST100 banner, Döviz widget, Altın widget
  - 30-second auto-refresh with independent per-widget loading and error state
  - Responsive 2-column grid collapsing to 1-column at ≤768px
  - Portfolio placeholder (empty state) ready for Plan 02 wiring

affects: [29-dashboard-plan-02, 30-kesif-hisse-detay]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Independent per-widget state buckets (bist100/forex/gold each with own loading+error state)
    - 1-second tick setInterval driving 30-second data refresh with countdown display
    - Null gold change_pct rendered as dash via PriceChange value={null}
    - Sub-components as local functions in page.tsx (ForexList, GoldList, ForexSkeleton, GoldSkeleton)

key-files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/page.tsx
    - frontend/src/app/page.module.css

key-decisions:
  - "Gold daily_change_pct unavailable from Phase 28 backend — render PriceChange value={null} to display em-dash per Pitfall 1 from RESEARCH.md"
  - "30s refresh implemented via 1s tick (not 30s interval) to drive countdown display — setInterval(tick, 1000) with secs counter"
  - "Forex pairs rendered in backend-dict order via forex.pairs array — no client-side resorting per Pitfall 5"
  - "Skeleton shown only on initial null state; background refresh leaves current data in place per Pitfall 3"

patterns-established:
  - "Pattern: append-only api.ts extension — new interfaces before export const api, new methods before closing };"
  - "Pattern: page.module.css is phase-scoped — full rewrite per phase, no accumulation of old classes"
  - "Pattern: per-widget independent fetch with individual .then/.catch/.finally chains (not Promise.allSettled)"

requirements-completed: [DASH-01, DASH-02, DASH-03]

# Metrics
duration: 2min
completed: 2026-05-07
---

# Phase 29 Plan 01: Dashboard — Piyasa Özeti Summary

**Türkçe Piyasa Özeti dashboard with BIST100 banner, 6-pair Döviz widget, 5-form Altın widget, and 30-second auto-refresh using independent per-widget state buckets**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-07T16:53:20Z
- **Completed:** 2026-05-07T16:55:50Z
- **Tasks:** 3 of 3
- **Files modified:** 3

## Accomplishments
- Extended api.ts with 4 TypeScript interfaces and 3 methods matching Phase 28 backend shapes (append-only, no existing code touched)
- Replaced 1346-line old page.module.css with 157-line focused Phase 29 stylesheet
- Replaced 510-line v3 dashboard page.tsx with clean 232-line Phase 29 implementation covering DASH-01, DASH-02, DASH-03
- Full-width BIST100 banner with endeks değeri (28px mono), renkli günlük değişim, formatVolume hacim
- Döviz widget: 6 pairs in backend order with Türkçe labels (Dolar/Avro/Sterlin/Çin Yuanı/Japon Yeni/İsviçre Frangı) + PriceChange arrows
- Altın widget: 5 forms in fixed order (gram/ons/çeyrek/yarım/tam) with ₺ price and "—" for unavailable change_pct
- 30s auto-refresh with per-second countdown display; proper clearInterval cleanup

## Task Commits

1. **Task 1: Append 3 market interfaces + 3 methods to api.ts** - `209a970` (feat)
2. **Task 2: Delete and rewrite page.module.css from scratch** - `49b6e7e` (feat)
3. **Task 3: Delete and rewrite page.tsx** - `e04a76f` (feat)

## Files Created/Modified
- `frontend/src/lib/api.ts` - Added MarketBist100Response, ForexPair, MarketForexResponse, MarketGoldResponse interfaces + getMarketBist100/getMarketForex/getMarketGold methods
- `frontend/src/app/page.tsx` - Full rewrite: Phase 29 Piyasa Özeti dashboard (232 lines, down from 510)
- `frontend/src/app/page.module.css` - Full rewrite: Phase 29 CSS module (157 lines, down from 1346)

## Decisions Made
- Gold daily_change_pct unavailable from Phase 28 backend — render `PriceChange value={null}` to display em-dash. Documented as intentional Phase 28 limitation.
- 30s refresh uses 1-second tick (not 30s interval) so the countdown display (`Otomatik yenileme: {N}s`) decrements smoothly each second.
- Forex pairs rendered in backend-dict order (forex.pairs as-is) — no client resorting per Pitfall 5 from RESEARCH.md.
- Skeleton shown only on initial load (data === null && loading === true); background refreshes leave current data visible.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

- `styles.portfolioPlaceholder` section renders "Portföy yönetimi yakında" empty state — intentional placeholder for Plan 02 (DASH-04). No live portfolio data wired. Plan 02 will replace this with real portfolio widget.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Dashboard at `/` fully functional for DASH-01, DASH-02, DASH-03
- Plan 02 (Portfolio widget, DASH-04) can replace `portfolioPlaceholder` section
- TypeScript clean, Next.js production build passes

---
*Phase: 29-dashboard*
*Completed: 2026-05-07*
