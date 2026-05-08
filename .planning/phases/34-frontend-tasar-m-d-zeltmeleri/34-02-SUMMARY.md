---
phase: 34-frontend-tasar-m-d-zeltmeleri
plan: "02"
subsystem: frontend
tags: [design, ui, model-portfolio, dashboard, cleanup, typescript]
dependency_graph:
  requires: ["34-01"]
  provides: ["DESIGN-03", "DESIGN-04", "DESIGN-05", "DESIGN-06"]
  affects: ["frontend/src/app/model-portfolio", "frontend/src/app/page", "frontend/src/lib/api", "frontend/src/components"]
tech_stack:
  added: []
  patterns: ["CSS custom properties (var(--bg-elevated))", "CSS Grid responsive layout", "TypeScript interface pruning"]
key_files:
  created: []
  modified:
    - frontend/src/app/model-portfolio/page.tsx
    - frontend/src/app/model-portfolio/page.module.css
    - frontend/src/app/page.tsx
    - frontend/src/app/page.module.css
    - frontend/src/lib/api.ts
  deleted:
    - frontend/src/components/SparklineWidget.tsx
decisions:
  - "Strategy cards use div elements (not Link) — no destination route exists for individual strategy pages"
  - "var(--bg-elevated) replaces hardcoded rgba(255,255,255,0.03) for theme-aware light/dark hover"
  - "Removed 7 orphan source-catalog/health interfaces and 2 sparkline interfaces — all were only consumed by deleted api methods or SparklineWidget"
metrics:
  duration: "~3 minutes"
  completed: "2026-05-08"
  tasks_completed: 3
  files_modified: 5
  files_deleted: 1
---

# Phase 34 Plan 02: Frontend Design Fixes Summary

**One-liner:** 6 strategy cards on model-portfolio, theme-aware hover, portfolio empty state, and dead code removal (SparklineWidget + 3 api methods + 9 orphan interfaces).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add 6 strategy cards to model-portfolio page | 20ebbd2 | page.tsx, page.module.css |
| 2 | Theme-aware hover fix + dashboard portfolio empty state | 36a591c | page.tsx, page.module.css |
| 3 | Delete SparklineWidget + remove dead api.ts methods and orphan interfaces | 31c31c2 | SparklineWidget.tsx (deleted), api.ts |

## DESIGN Requirements Addressed

### DESIGN-03: 6 Strategy Cards (model-portfolio)

Added `STRATEGIES` constant array with exactly 6 entries and rendered them in a responsive `strategyGrid` section below `AiPortfolioSection`.

Strategy names: Temettü Avcısı, Büyüme Lokomotifleri, Defansif Kalkan, Momentum, Değer Yatırımı, Karma

Each card shows: icon, name, description, badge (with accent color border). Cards are `<div>` elements — not `<Link>` since no destination routes exist.

### DESIGN-04: Theme-Aware Hover Fix (dashboard)

Replaced `.stockRow:hover { background: rgba(255, 255, 255, 0.03); }` with `.stockRow:hover { background: var(--bg-elevated); }` in `frontend/src/app/page.module.css`.

`--bg-elevated` is `#1c1f24` (dark) and `#f4f4f5` (light) — both give proper visible hover in both themes.

### DESIGN-05: Dead Code Removal

**File deleted:** `frontend/src/components/SparklineWidget.tsx`

**api.ts methods removed:**
- `getSourceCatalog`
- `getSourceHealthHistory`
- `scanSource`

**api.ts interfaces removed:**
- `SourceCatalogItem`
- `SourceCatalogResponse`
- `SourceHealthHistoryItem`
- `SourceHealthHistoryResponse`
- `SourceHealthAlertItem`
- `SourceHealthRollupItem`
- `SourceHealthDashboardResponse`
- `SparklinePoint`
- `SparklineResponse`

**Preserved intact:** `HealthResponse`, `HealthSourceStatus`, and all Market/Portfolio/ModelPortfolio/Intelligence/StockSummary types.

### DESIGN-06: Portfolio Empty State (dashboard)

Replaced single `<Link>Pozisyon ekle</Link>` with a richer block:
```tsx
<div className={styles.portfolioEmpty}>
  <p className={styles.portfolioEmptyText}>Henüz portföy eklenmedi.</p>
  <Link href="/portfolio" className={styles.emptyLink}>Pozisyon ekle →</Link>
</div>
```

Added `.portfolioEmpty` and `.portfolioEmptyText` CSS rules. Populated positions branch (positions.length > 0) is unchanged.

## Verification Results

```
# TypeScript build (all 3 tasks):
cd frontend && npx tsc --noEmit → exit 0 (zero errors)

# SparklineWidget deleted:
test ! -f frontend/src/components/SparklineWidget.tsx → PASS

# No stray imports:
grep -rn "SparklineWidget" frontend/src/ → 0 matches

# Dead api.ts methods removed:
grep -n "getSourceCatalog|scanSource|getSourceHealthHistory" api.ts → 0 matches

# All 6 strategy names in page.tsx:
grep -c "Temettü Avcısı|..." → 6

# Hover rule updated:
grep -n ".stockRow:hover { background: var(--bg-elevated)" → 1 match

# Empty state text:
grep -n "Henüz portföy eklenmedi" page.tsx → 1 match

# HealthResponse preserved:
grep -n "interface HealthResponse" api.ts → 1 match (line 101)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all design fixes are fully implemented with no placeholder content.

## Self-Check: PASSED

- `frontend/src/app/model-portfolio/page.tsx` — FOUND
- `frontend/src/app/model-portfolio/page.module.css` — FOUND
- `frontend/src/app/page.tsx` — FOUND
- `frontend/src/app/page.module.css` — FOUND
- `frontend/src/lib/api.ts` — FOUND
- `frontend/src/components/SparklineWidget.tsx` — CONFIRMED DELETED
- Commits 20ebbd2, 36a591c, 31c31c2 — FOUND in git log
