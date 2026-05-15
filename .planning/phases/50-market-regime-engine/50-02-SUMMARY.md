---
phase: 50-market-regime-engine
plan: "02"
subsystem: frontend
tags: [market-regime, badge, typescript, react, dashboard, stock-detail]
dependency_graph:
  requires: [50-01]
  provides: [REJ-02]
  affects: [frontend/src/app/page.tsx, frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [inline-component, non-blocking-fetch, css-modules]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/page.tsx
    - frontend/src/app/page.module.css
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - RegimeBadge defined inline in each page file rather than as a shared component, per plan spec
  - Badge silently absent (null state) when backend returns 404 or network error, no error state rendered
  - Turkish regime names used as colorMap keys (Boga/Ayi/etc.) with fallback to var(--text-muted)
metrics:
  duration: "~5 minutes"
  completed: "2026-05-15"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 5
requirements:
  - REJ-02
---

# Phase 50 Plan 02: Frontend Regime Badge Summary

MarketRegimeResponse TypeScript interface and api.getMarketRegime() method added to api.ts; inline RegimeBadge component wired to dashboard (after marketFacts) and stock detail (heroLeft after quick stats), with CSS module styles in both pages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | MarketRegimeResponse type + api.getMarketRegime() | 92070dc | frontend/src/lib/api.ts |
| 2 | Dashboard + stock detail RegimeBadge | f07e9dd | page.tsx, page.module.css (x2), stock detail page.tsx + page.module.css |

## What Was Built

### Task 1 — api.ts type + fetch method
- Added `export interface MarketRegimeResponse` with fields: `regime`, `date`, `adx`, `ema200`, `atr`
- Added `getMarketRegime: () => apiFetch<MarketRegimeResponse>('/market-regime')` to the `api` export object
- Placed in the Market Interfaces section near `getMarketBist100History`

### Task 2 — Dashboard regime badge
- Added `MarketRegimeResponse` to named imports in `frontend/src/app/page.tsx`
- Added `const [regime, setRegime] = useState<MarketRegimeResponse | null>(null)` state
- In `load` useCallback: `api.getMarketRegime().then(setRegime).catch(() => null)`
- `<RegimeBadge regime={regime} />` placed after the `<div className={styles.marketFacts}>` block in heroLeft
- `RegimeBadge` function component defined after `AssetRow` at the bottom of the file
- CSS `.regimeBadge` (inline-flex pill with border) and `.regimeDot` (8px circle) added to `page.module.css`

### Task 2 — Stock detail regime badge
- Added `MarketRegimeResponse` to named imports in stock detail `page.tsx`
- Added `regime` state alongside existing state declarations
- In `loadStock()` non-blocking fetches section: `api.getMarketRegime().then(setRegime).catch(() => null)`
- `<RegimeBadge regime={regime} />` placed after `<div className={styles.heroQuickStats}>` in heroLeft
- Same `RegimeBadge` component definition added after `ScoreBar` component
- Same `.regimeBadge` and `.regimeDot` CSS added to stock detail `page.module.css`

## RegimeBadge Color Mapping

| Regime | Color |
|--------|-------|
| Boga | var(--accent-green) |
| Ayi | var(--accent-red) |
| Yatay | var(--text-muted) |
| Volatil | #f59e0b (amber) |
| (fallback) | var(--text-muted) |

## Verification Results

- `grep -q 'export interface MarketRegimeResponse' frontend/src/lib/api.ts` — PASS
- `grep -q 'getMarketRegime' frontend/src/lib/api.ts` — PASS
- `grep -c 'RegimeBadge' frontend/src/app/page.tsx` — 3 (function def + JSX usage + type annotation)
- `grep -q 'getMarketRegime' frontend/src/app/page.tsx` — PASS
- `grep -q '.regimeBadge' frontend/src/app/page.module.css` — PASS
- `grep -c 'RegimeBadge' frontend/src/app/stocks/[symbol]/page.tsx` — 3
- `grep -q 'getMarketRegime' frontend/src/app/stocks/[symbol]/page.tsx` — PASS
- `grep -q '.regimeBadge' frontend/src/app/stocks/[symbol]/page.module.css` — PASS
- `npx tsc --noEmit` — PASS (zero errors)
- `npm run lint` — PASS (zero warnings)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data flows from `api.getMarketRegime()` to `regime` state to `RegimeBadge` component. Badge is silently absent when state is null (API unavailable or no data yet), which is the intended behavior per REJ-02.

## Self-Check: PASSED

- `frontend/src/lib/api.ts` — MarketRegimeResponse and getMarketRegime present
- `frontend/src/app/page.tsx` — RegimeBadge function and JSX usage present
- `frontend/src/app/page.module.css` — .regimeBadge CSS present
- `frontend/src/app/stocks/[symbol]/page.tsx` — RegimeBadge function and JSX usage present
- `frontend/src/app/stocks/[symbol]/page.module.css` — .regimeBadge CSS present
- Commits 92070dc and f07e9dd exist in git log
