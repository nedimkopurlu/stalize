---
phase: 05-ui-redesign
plan: 05-05
title: "Score Table Score-Range Filter"
subsystem: frontend
tags: [filter, ui, score-range, stocks-table, UIUX-03]
requirements: [UIUX-03]

dependency_graph:
  requires: [05-01]
  provides: [score-range-filter, temel-algi-columns]
  affects: [frontend/src/app/stocks/page.tsx]

tech_stack:
  added: []
  patterns:
    - Frontend-only derived filter array (stocks.filter) on top of backend-sorted results
    - Empty-string sentinel for optional number inputs (number | '' state type)
    - Composed filters: recommendation runs on backend, score range runs on frontend

key_files:
  created: []
  modified:
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/[symbol]/page.tsx

decisions:
  - minScore/maxScore use `number | ''` state (not `number`) so inputs can be blank without showing 0
  - Score range filter is frontend-only — backend already pre-filters by recommendation and sorts by overall_score; filtered array preserves sort order
  - filterRec continues to be passed as API query param (not moved to frontend) — keeps recommendation filter fast even with large datasets

metrics:
  duration_minutes: 12
  completed: "2026-04-18T00:02:59Z"
  tasks_completed: 1
  files_modified: 2
---

# Phase 5 Plan 05: Score Table Score-Range Filter Summary

Frontend-only score range filter (Min/Max Skor) on /stocks table with Temel and Algi score ring columns added.

## What Was Built

Added `minScore` / `maxScore` state variables and a `filtered` derived array to `/stocks` page. The filter bar now shows two number inputs (Min Skor, Max Skor) between the recommendation select and the BIST30 toggle. Filtering is instant on `onChange` — no submit button. The results count updates to show `{filtered.length} / {total} hisse`.

Two new score ring columns were added to the table — Temel (fundamental_score) and Algi (sentiment_score) — both using `<ScoreRing>` with `hide-mobile` class, inserted between Teknik and Nedensellik columns.

## Filter Logic Pattern

```typescript
// Backend handles: sort_by, recommendation, search, bist30 — passed as API params
// Frontend handles: score range — applied to already-fetched stocks array

const filtered = stocks.filter((s) => {
  if (minScore !== '' && (s.overall_score ?? 0) < minScore) return false;
  if (maxScore !== '' && (s.overall_score ?? 0) > maxScore) return false;
  return true;
});
```

Both filters compose: if recommendation=AL is active (backend pre-filters), then score range further narrows the AL stocks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing ScoreRing import in [symbol]/page.tsx**
- **Found during:** TypeScript build verification
- **Issue:** `[symbol]/page.tsx` used `ScoreRing` in JSX but had no import — TS2304 error
- **Fix:** Added `import ScoreRing from '@/components/ScoreRing'` — however, inspection revealed ScoreRing was imported but not directly used in JSX (ScoreLayerPanel wraps it). Import was added then found unused. Actual fix was different: see item 2.
- **Files modified:** frontend/src/app/stocks/[symbol]/page.tsx
- **Commit:** 0707a55d

**2. [Rule 1 - Bug] chartRef undeclared in [symbol]/page.tsx**
- **Found during:** TypeScript build verification
- **Issue:** `<div ref={chartRef} className={styles.chartCanvas} />` — `chartRef` was never declared; should have been `<CandlestickPanel>` (which was imported but unused). Pre-existing bug from Phase 05-04.
- **Fix:** Replaced `<div ref={chartRef} ...>` with `<CandlestickPanel prices={prices?.prices ?? []} />` — wires the already-imported component correctly
- **Files modified:** frontend/src/app/stocks/[symbol]/page.tsx
- **Commit:** 0707a55d

## Self-Check

- [x] `frontend/src/app/stocks/page.tsx` exists and modified
- [x] `frontend/src/app/stocks/[symbol]/page.tsx` exists and fixed
- [x] Commit `0707a55d` exists
- [x] `npm run build` exits 0 — all 12 pages generated
- [x] `npx tsc --noEmit` exits 0 — no TypeScript errors

## Self-Check: PASSED

## Checkpoint Status

Task 1 (auto) — COMPLETE and committed.
Task 2 (checkpoint:human-verify) — Awaiting human verification of all four UIUX requirements end-to-end (see plan for 18-point checklist).
