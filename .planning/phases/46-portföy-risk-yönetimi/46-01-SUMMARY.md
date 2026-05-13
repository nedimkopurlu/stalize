---
phase: 46-portföy-risk-yönetimi
plan: "01"
subsystem: frontend/portfolio
tags: [risk, portfolio, sector-distribution, ui]
dependency_graph:
  requires: []
  provides: [riskGuard-state, sectorDist-section, riskRows-top3-sectors]
  affects: [frontend/src/app/portfolio/page.tsx, frontend/src/app/portfolio/page.module.css]
tech_stack:
  added: []
  patterns: [useEffect-derived-value, parallel-fetch, CSS-bar-chart]
key_files:
  created: []
  modified:
    - frontend/src/app/portfolio/page.tsx
    - frontend/src/app/portfolio/page.module.css
decisions:
  - "riskGuard fetched in separate useEffect depending on [positions, loadingPositions] — totalValue computed after positions load"
  - "safeValue fallback 100000 when portfolio is empty — matches api default"
  - "sectorDist section placed between heroGrid and watchSection — per plan spec"
  - "Top-3 sectors highlighted with sectorRowTop CSS class (font-weight 600)"
  - "Empty sector string shows 'Bilinmiyor' fallback"
metrics:
  duration_minutes: 8
  completed_date: "2026-05-14"
  tasks_completed: 3
  files_changed: 2
---

# Phase 46 Plan 01: Portföy Risk — Sektör Dağılımı & Risk Özet Kartı Summary

**One-liner:** PortfolioRiskResponse fetch + yatay bar chart sektör dağılımı + risk özet kartına açık pozisyon sayısı ve en büyük 3 sektör satırı eklendi (RISK-01, RISK-04).

## What Was Built

### riskGuard state + fetch (Task 1)

- `PortfolioRiskResponse` imported from `@/lib/api`
- `riskGuard` and `loadingRiskGuard` state added to `PortfolioPage`
- `fetchRiskGuard(totalValue)` function: calls `api.getPortfolioRiskGuard(safeValue)`, silently skips on error (matches `fetchHistory` pattern)
- `useEffect([positions, loadingPositions])`: computes `totalValue` from active positions after load, then calls `fetchRiskGuard`

### Sektör Dağılımı section (Task 2)

- New `<section className={styles.sectorDist}>` inserted between heroGrid and watchSection
- Renders a sorted (desc by `exposure_pct`) list of sectors from `riskGuard.sector_exposure`
- Each sector row: name (left) + horizontal CSS bar (width = `exposure_pct%`) + percentage (right)
- First 3 sectors receive `sectorRowTop` class (bold sector name)
- Loading state: "Sektör dağılımı yükleniyor…"
- Empty state: "Sektör dağılımı için aktif pozisyon gerekli"

### Risk Özet Kartı — yeni satırlar (Task 3)

- "Aktif pozisyon" row replaced with "Açık pozisyon: {activePositions.length} hisse"
- New "En büyük 3 sektör" row: shows top-3 from `riskGuard.sector_exposure` sorted desc, formatted as "Bankacılık %42, Enerji %18, Sanayi %15"
- Loading/empty fallbacks implemented

## Files Touched

| File | Change |
|------|--------|
| `frontend/src/app/portfolio/page.tsx` | Added import, state, fetchRiskGuard, useEffect, sectorDist section, updated riskRow, added En büyük 3 sektör row |
| `frontend/src/app/portfolio/page.module.css` | Added sectorDist, sectorList, sectorRow, sectorRowTop, sectorName, sectorBar, sectorBarFill, sectorPct, riskRowSectors, riskRowSectorList CSS classes |

## Commits

| Task | Hash | Message |
|------|------|---------|
| Task 1 | 74e7b2f | feat(46-01): riskGuard state + fetch with totalValue |
| Task 2 | 139d2a1 | feat(46-01): sektör dağılımı bölümü yatay bar chart (RISK-01) |
| Task 3 | b923076 | feat(46-01): risk özet kartı — açık pozisyon + en büyük 3 sektör (RISK-04) |

## Deviations from Plan

None — plan executed exactly as written.

## Notes for Plan 02

- `riskGuard` state is now available in `portfolio/page.tsx`; Plan 02 (yoğunlaşma uyarıları, RISK-02, RISK-03) can read `riskGuard.sector_exposure[n].status` and `riskGuard.cash_action` to render inline warnings
- `loadingRiskGuard` boolean available for conditional rendering in Plan 02
- No new API endpoint needed — `getPortfolioRiskGuard` already fetches concentration data in `rules` and `sector_exposure.status` fields

## Known Stubs

None — all data is wired from the real API endpoint (`/risk/portfolio`).

## Self-Check: PASSED

- `frontend/src/app/portfolio/page.tsx` — modified (confirmed via grep checks)
- `frontend/src/app/portfolio/page.module.css` — modified (confirmed via grep checks)
- Commits 74e7b2f, 139d2a1, b923076 — exist in git log
- TypeScript: `npx tsc --noEmit` — 0 errors
