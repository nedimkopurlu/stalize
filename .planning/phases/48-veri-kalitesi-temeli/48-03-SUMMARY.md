---
phase: 48-veri-kalitesi-temeli
plan: "03"
subsystem: frontend
tags: [data-quality, ui, typescript, css, vkl-01, vkl-02]
dependency_graph:
  requires:
    - "48-01"  # backend data_quality_score field
    - "48-02"  # safeLabel centralized in StockHelpers
  provides:
    - frontend-quality-badge
    - frontend-quality-detail-row
  affects:
    - frontend/src/app/stocks/page.tsx
    - "frontend/src/app/stocks/[symbol]/page.tsx"
tech_stack:
  added: []
  patterns:
    - conditional render guard (data_quality_score != null)
    - CSS custom properties for semantic color (--accent-red/yellow/green)
    - threshold-based CSS class selection
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/page.module.css
    - "frontend/src/app/stocks/[symbol]/page.tsx"
    - "frontend/src/app/stocks/[symbol]/page.module.css"
decisions:
  - "Used breakdownBar/breakdownBarHeader/breakdownBarMeta existing CSS classes for the Veri Güven Skoru row in detail page to stay consistent with the existing skor dökümü layout"
  - "Quality badge placed inside the Görünüm column td alongside recommendation label (inline after safeLabel span) to keep table column count unchanged"
metrics:
  duration: "~10 minutes"
  completed: "2026-05-15T05:41:40Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 5
---

# Phase 48 Plan 03: Veri Kalitesi Frontend UI Summary

**One-liner:** Colored "DK: NN" quality badge in stocks list + "Veri Güven Skoru: NN/100" row with "Düşük Veri Güveni" warning in stock detail page, using threshold-based CSS (red < 50, yellow 50-75, green > 75).

## Objective

Surface the backend `data_quality_score` (added in Plan 48-01) in the frontend: typed in `api.ts`, colored pill badge in the stocks list, and a "Veri Güven Skoru" row plus "Düşük Veri Güveni" warning in the stock detail page.

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Verify/add data_quality_score to StockSummary type | Complete (already present) | ad2a9f9 |
| 2 | Render data quality badge in stocks list rows | Complete | ad2a9f9 |
| 3 | Add Veri Güven Skoru row to stock detail skor dökümü | Complete | ad2a9f9 |

## Files Modified

### frontend/src/lib/api.ts
- Verified `data_quality_score?: number | null` already existed at line 55 in `StockSummary` interface.
- The `StockDetail` interface (`StockSummary & {...}`) inherits it automatically — no addition needed.

### frontend/src/app/stocks/page.tsx
- Added quality badge JSX inside the "Görünüm" column `<td>` immediately after the `safeLabel(stock.recommendation)` span.
- Badge only renders when `stock.data_quality_score != null`.
- Color class: `qualityLow` (< 50), `qualityMid` (50-75), `qualityHigh` (> 75).
- Tooltip shows "Düşük Veri Güveni: ..." for low scores, "Veri Güven Skoru: NN/100" otherwise.

### frontend/src/app/stocks/page.module.css
- Appended 4 new CSS classes: `.qualityBadge`, `.qualityLow`, `.qualityMid`, `.qualityHigh`.
- Uses `--accent-red`, `--accent-yellow`, `--accent-green` CSS custom properties.

### frontend/src/app/stocks/[symbol]/page.tsx
- Added a `<div className={styles.breakdownBar}>` block at the end of the skor dökümü section (before `breakdownNote`).
- Renders only when `s.data_quality_score != null`.
- Shows colored "NN/100" value + "Düşük Veri Güveni" warning span when score < 50.

### frontend/src/app/stocks/[symbol]/page.module.css
- Appended 4 new CSS classes: `.qualityLow`, `.qualityMid`, `.qualityHigh`, `.qualityWarning`.
- No duplicate classes (confirmed via grep before adding).

## Verification Results

```
grep -E 'data_quality_score\?.*number.*null' frontend/src/lib/api.ts    => PASS (2 matches: line 55, line 488)
grep -q 'qualityBadge' frontend/src/app/stocks/page.module.css          => PASS
grep -q 'qualityLow'   frontend/src/app/stocks/page.module.css          => PASS
grep -q 'qualityMid'   frontend/src/app/stocks/page.module.css          => PASS
grep -q 'qualityHigh'  frontend/src/app/stocks/page.module.css          => PASS
grep -q 'data_quality_score' frontend/src/app/stocks/page.tsx           => PASS
grep -q 'Veri Güven Skoru'  frontend/src/app/stocks/[symbol]/page.tsx   => PASS
grep -q 'Düşük Veri Güveni' frontend/src/app/stocks/[symbol]/page.tsx   => PASS
grep -q 'data_quality_score' frontend/src/app/stocks/[symbol]/page.tsx  => PASS
cd frontend && npx tsc --noEmit                                          => PASS (exit 0)
cd frontend && npm run lint                                              => PASS (exit 0)
```

## Deviations from Plan

None — plan executed exactly as written.

Task 1 was pre-satisfied: `StockSummary.data_quality_score` was already declared in `api.ts` at line 55 from a prior session. No modification was needed.

For Task 3, the plan suggested using `scoreRow`/`scoreLabel`/`scoreValue` CSS classes. After reading the actual file, the skor dökümü section uses `breakdownBar`/`breakdownBarHeader`/`breakdownBarMeta`/`breakdownBarLabel` classes. Used the existing classes for visual consistency — this is a Rule 1 (auto-fix) correction, not a deviation.

## Known Stubs

None. The `data_quality_score` field flows directly from the backend API response through the typed interface to the render layer. No hardcoded or mock values.

## Self-Check: PASSED

- [x] `frontend/src/app/stocks/page.tsx` — file modified with quality badge JSX
- [x] `frontend/src/app/stocks/page.module.css` — 4 quality CSS classes appended
- [x] `frontend/src/app/stocks/[symbol]/page.tsx` — Veri Güven Skoru row added
- [x] `frontend/src/app/stocks/[symbol]/page.module.css` — 4 quality CSS classes appended
- [x] Commit `ad2a9f9` verified via git log
