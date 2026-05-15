---
phase: 52-portfoy-analizi
plan: "02"
subsystem: frontend
tags: [portfolio, analytics, beta, correlation, position-sizing, typescript]
dependency_graph:
  requires: [52-01]
  provides: [portfolio-beta-ui, correlation-matrix-ui, position-sizing-ui]
  affects: [frontend/src/lib/api.ts, frontend/src/app/portfolio/page.tsx, frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [non-blocking-fetch, null-guard-render, useState-useCallback, CSS-modules]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/portfolio/page.tsx
    - frontend/src/app/portfolio/page.module.css
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - "Analytics fetch is non-blocking (silent catch) — page renders even if /portfolio/analytics fails"
  - "Position sizing uses portfolio value computed from active positions sum; fallback 100000 when empty"
  - "Analytics section inserted between Sektör Dağılımı and Takip Listesi sections"
  - "Position sizing card inserted between score breakdown and investment thesis sections"
metrics:
  duration: "~15 minutes"
  completed_date: "2026-05-15T16:52:28Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 5
---

# Phase 52 Plan 02: Frontend Portfolio Analytics Wire-up Summary

**One-liner:** Wired portfolio beta + NxN correlation matrix to portfolio page and ATR-based position sizing card to stock detail page, using non-blocking fetches with null-guard rendering.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add TypeScript interfaces and api methods | fce1f16 | frontend/src/lib/api.ts |
| 2 | Portfolio page — beta display + correlation matrix | 446906f | portfolio/page.tsx, portfolio/page.module.css |
| 3 | Stock detail page — position sizing card | bc25d89 | stocks/[symbol]/page.tsx, stocks/[symbol]/page.module.css |

## What Was Built

### Task 1 — api.ts type extensions

Three new exported interfaces added to `frontend/src/lib/api.ts`:

- `PortfolioCorrelationMatrix` — `{ symbols: string[]; matrix: number[][]; excluded_symbols: string[] }`
- `PortfolioAnalyticsResponse` — `{ beta: number | null; correlation_matrix: PortfolioCorrelationMatrix | null; calculated_at: string }`
- `PositionSizeResponse` — full position sizing response with atr_14, stop_distance, risk amounts, max shares

Two new api methods added to the `api` object:

- `getPortfolioAnalytics()` — `GET /portfolio/analytics`
- `getPositionSize(symbol, portfolioValue)` — `GET /stocks/{symbol}/position-size?portfolio_value={n}`

### Task 2 — Portfolio page beta + correlation matrix

**page.tsx changes:**
- Added `PortfolioAnalyticsResponse` to imports
- Added `analytics` and `loadingAnalytics` state variables
- Added `fetchAnalytics()` non-blocking function (same pattern as `fetchHistory`)
- Called `fetchAnalytics()` in initial `useEffect`
- Inserted new `<section className={styles.analyticsSection}>` with two-column grid:
  - Beta card: displays numeric beta value, Piyasadan Daha Volatil/Savunmacı tag, descriptive text, benchmark note
  - Correlation matrix card: renders NxN table with yellow cell highlight for |r|>0.7 pairs, excluded symbols note
  - Both cards degrade gracefully: loading state, null state with contextual message

**page.module.css additions:**
- `analyticsSection`, `analyticsGrid` (responsive 2→1 col at 900px), `analyticsCard`
- `analyticsTitle`, `betaValue`, `betaTag`, `betaTagHigh`, `betaTagLow`, `betaDesc`, `betaNote`
- `corrTableWrap`, `corrTable`, `corrHeader`, `corrRowLabel`, `corrCell`, `corrCellDiag`, `corrCellHigh`, `corrNote`

### Task 3 — Stock detail position sizing card

**page.tsx changes:**
- Added `PositionSizeResponse` to imports
- Added `positionSize` state: `useState<PositionSizeResponse | null>(null)`
- In `loadStock` useCallback, added non-blocking chain after `getMarketRegime()`:
  - Fetches `getPortfolioPositions()`, computes total value from active positions (is_active !== false)
  - Falls back to 100000 when portfolio is empty
  - Calls `getPositionSize(symbol, portfolioValue)` and sets state
  - Silent catch sets positionSize to null
- Inserted `{positionSize && (...)}` guarded section before the investment thesis section
  - Shows: Güncel Fiyat, ATR 14 gün, Stop Mesafesi (ATR×2), Portföy Değeri in 4-column grid
  - Shows %1 Risk and %2 Risk columns (amount + max lot count) side-by-side
  - Footer note explaining ATR×2 stop methodology

**page.module.css additions:**
- `positionSizeSection`, `positionSizeCard`, `positionSizeEyebrow`, `positionSizeTitle`
- `positionSizeGrid` (4-col responsive → 2-col at 700px), `positionSizeItem`, `positionSizeLabel`, `positionSizeValue`
- `positionSizeRiskGrid`, `positionSizeRiskCol`, `positionSizeRiskDivider`, `positionSizeRiskLabel`, `positionSizeRiskAmount`, `positionSizeRiskShares`
- `positionSizeNote`

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is wired to live backend endpoints. The card is hidden when positionSize is null (no placeholder text shown to user).

## Self-Check: PASSED

Files exist:
- FOUND: frontend/src/lib/api.ts (PortfolioAnalyticsResponse, PositionSizeResponse present)
- FOUND: frontend/src/app/portfolio/page.tsx (analytics section present)
- FOUND: frontend/src/app/portfolio/page.module.css (analyticsSection, corrTable present)
- FOUND: frontend/src/app/stocks/[symbol]/page.tsx (positionSize card present)
- FOUND: frontend/src/app/stocks/[symbol]/page.module.css (positionSizeCard present)

Commits exist:
- fce1f16 — feat(52-02): add interfaces and api methods
- 446906f — feat(52-02): portfolio beta and correlation matrix
- bc25d89 — feat(52-02): position sizing card on stock detail

TypeScript: `npx tsc --noEmit` exits 0
ESLint: `npm run lint` exits 0
