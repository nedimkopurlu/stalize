---
phase: 49-veri-zenginlestirme
plan: "02"
subsystem: frontend
tags: [badges, liquidity, kap, circuit-breaker, typescript]
dependency_graph:
  requires: [49-01]
  provides: [VKL-03, VKL-04, KAP-02]
  affects: [frontend/src/app/stocks, frontend/src/lib/api.ts]
tech_stack:
  added: []
  patterns: [conditional-badge-rendering, css-modules, typescript-interface-extension]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/page.module.css
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - "Used 9.8 threshold (not 10.0) for BIST circuit-breaker detection — matches BIST behavior where limit fires slightly before 10%"
  - "Omit high-liquidity badge; only düşük and orta shown — yüksek is default, no badge needed"
  - "KAP category badge placed before <strong>{title}</strong> inside NewsRow content block for visual hierarchy"
metrics:
  duration_minutes: 8
  completed_date: "2026-05-15T06:05:06Z"
  tasks_completed: 3
  files_modified: 5
---

# Phase 49 Plan 02: Frontend Badges — Tavan/Taban, Likidite, KAP Kategorisi

**One-liner:** Inline TAVAN/TABAN circuit-breaker badges, Amihud liquidity tier badges, and color-coded KAP category badges added to stock list and detail pages via CSS Modules.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Update api.ts type contracts | dcbc545 | frontend/src/lib/api.ts |
| 2 | Stock list — tavan/taban + liquidity badges | fb9440a | stocks/page.tsx, stocks/page.module.css |
| 3 | Stock detail — tavan/taban + liquidity section + KAP badges | 2a3d245 | [symbol]/page.tsx, [symbol]/page.module.css |

## What Was Built

### Task 1 — api.ts Type Contracts
- `StockSummary.liquidity_score` type corrected from `number | null` to `string | null` (backend returns `"yüksek" | "orta" | "düşük"`)
- `StockSummary.amihud_ratio?: number | null` added
- `StockNewsItem.kap_category?: string | null` added

### Task 2 — Stock List Badges (stocks/page.tsx)
- **TAVAN badge** (green, solid): rendered inline in `daily_change_pct` cell when `>= 9.8`
- **TABAN badge** (red, solid): rendered inline when `<= -9.8`
- **Düşük Lik. badge** (red outline): rendered in Görünüm/score column when `liquidity_score === 'düşük'`
- **Orta Lik. badge** (amber outline): rendered when `liquidity_score === 'orta'`
- CSS classes added: `tavanBadge`, `tabanBadge`, `liquidityBadgeLow`, `liquidityBadgeMedium`

### Task 3 — Stock Detail Page (stocks/[symbol]/page.tsx)
- **Tavan/Taban badge** added inside `.heroPrice` block after the daily change display
- **Liquidity row** added after "Veri Güven Skoru" in score breakdown section — shows level badge (Yüksek/Orta/Düşük Likidite) color-coded
- **Liquidity warning banner** shown below the row when `liquidity_score === 'düşük'`
- **kapCategoryBadgeClass()** helper function added before `NewsRow` — maps category strings to CSS modifier classes
- **KAP category badge** rendered before `<strong>{item.title}</strong>` in `NewsRow` when `item.kap_category` is non-null
- Category color mapping:
  - High-impact (`İçeriden Öğrenme`, `Hukuki`, `Sermaye Artırımı`) → red badge
  - Positive (`Temettü`, `Pay Geri Alımı`) → green badge
  - `Finansal Sonuçlar` → amber badge
  - Others → gray/muted badge
- CSS classes added: `tavanBadge`, `tabanBadge`, `liquidityRow`, `liquidityWarning`, `liquidityBadge`, `liquidityBadgeLow`, `liquidityBadgeMedium`, `liquidityBadgeHigh`, `kapCategoryBadge`, `kapCategoryBadgeDefault`, `kapCategoryBadgeHighImpact`, `kapCategoryBadgePositive`, `kapCategoryBadgeAmber`

## Verification

- `grep 'kap_category' frontend/src/lib/api.ts` — PASS
- `grep 'amihud_ratio' frontend/src/lib/api.ts` — PASS
- `grep 'tavanBadge' frontend/src/app/stocks/page.tsx` — PASS
- `grep 'liquidity_score' frontend/src/app/stocks/[symbol]/page.tsx` — PASS
- `grep 'kap_category' frontend/src/app/stocks/[symbol]/page.tsx` — PASS
- `grep 'kapCategoryBadge' frontend/src/app/stocks/[symbol]/page.module.css` — PASS
- `npx tsc --noEmit` — PASS (no errors)
- `npm run lint` — PASS (no errors)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all badge logic wires directly to `StockSummary.liquidity_score`, `StockSummary.daily_change_pct`, and `StockNewsItem.kap_category` fields. Data availability depends on Phase 49-01 backend changes being deployed.

## Self-Check: PASSED

- `frontend/src/lib/api.ts` — FOUND: amihud_ratio, kap_category, liquidity_score as string
- `frontend/src/app/stocks/page.tsx` — FOUND: tavanBadge, tabanBadge, liquidityBadgeLow
- `frontend/src/app/stocks/page.module.css` — FOUND: tavanBadge, tabanBadge, liquidityBadgeLow, liquidityBadgeMedium
- `frontend/src/app/stocks/[symbol]/page.tsx` — FOUND: tavanBadge, tabanBadge, liquidity_score, kap_category
- `frontend/src/app/stocks/[symbol]/page.module.css` — FOUND: kapCategoryBadge and all badge classes
- Commits: dcbc545, fb9440a, 2a3d245 — all verified present
