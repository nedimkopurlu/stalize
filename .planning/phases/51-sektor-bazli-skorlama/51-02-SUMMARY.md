---
phase: 51-sektor-bazli-skorlama
plan: "02"
subsystem: frontend
tags: [typescript, sector-scoring, stock-detail, ui]
dependency_graph:
  requires: [51-01]
  provides: [frontend-sector-type-contracts, stock-detail-sector-ui]
  affects: [frontend/src/lib/api.ts, frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [optional-chaining-null-guard, reuse-existing-css-classes]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/[symbol]/page.tsx
decisions:
  - "Reused existing liquidityRow and breakdownMissingAlert CSS classes instead of new ones — visual consistency without CSS additions"
  - "Placed sector block after liquidity warning rows, before breakdownNote paragraph — maintains logical grouping"
  - "Used scoreBreakdown root fields (not bd alias) for sector fields since they sit outside the breakdown nested object"
metrics:
  duration_minutes: 5
  completed_at: "2026-05-15T16:35:15Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 51 Plan 02: Frontend Sector Scoring Type Contracts and Stock Detail UI Summary

Extended TypeScript type contracts and stock detail Skor Dökümü section to surface sector-specific scoring information for banka, GYO, and holding stocks.

## What Was Built

**Task 1 — api.ts type extensions** (commit `d62e0ea`):
- Added `sector_category?: string | null` and `nav_discount?: number | null` to `StockSummary` interface
- Added `sector_category?`, `sector_scoring_method?`, and `nav_discount?` to `ScoreBreakdownResponse` interface
- All fields optional — backward compatible with existing cached responses and non-sector stocks

**Task 2 — Stock detail Skor Dökümü sector block** (commit `7b5ec6e`):
- "Skorlama Yöntemi" row rendered via `liquidityRow` CSS class when `sector_scoring_method` is set (any sector)
- GYO note ("Gerçek NAD verisi mevcut değil; P/D değeri NAD yaklaşımı olarak kullanılmıştır.") shown via `breakdownMissingAlert` class with info icon
- Holding NAV iskonto row with color coding: green when discount > 15%, red when premium (negative), muted otherwise
- Holding approximation note rendered as secondary `breakdownNote`
- Block positioned after liquidity rows and before the main `breakdownNote` paragraph
- All conditionals null-guarded via optional chaining (`scoreBreakdown?.sector_category`)

## Deviations from Plan

None — plan executed exactly as written. Used `liquidityRow` and `breakdownMissingAlert` existing CSS classes instead of new `.sectorScoringBlock` per plan context note (plan interface section specified reusing these classes, orchestrator prompt suggested new classes; plan file context took precedence as it matched the existing codebase pattern).

## Verification Results

- `npx tsc --noEmit` — passed with no errors
- `npm run lint` — passed with no warnings
- `grep -q 'sector_category' frontend/src/lib/api.ts` — PASS
- `grep -q 'sector_category' frontend/src/app/stocks/[symbol]/page.tsx` — PASS
- `grep -q 'NAV İskontosu' page.tsx` — PASS
- `grep -q 'Gerçek NAD verisi' page.tsx` — PASS

## Known Stubs

None — all sector fields flow from backend `ScoreBreakdownResponse`; blocks are conditionally hidden when fields are null, which is correct behavior for non-sector stocks.

## Self-Check: PASSED

- `frontend/src/lib/api.ts` — modified, commit d62e0ea confirmed
- `frontend/src/app/stocks/[symbol]/page.tsx` — modified, commit 7b5ec6e confirmed
- Both commits present in git log
