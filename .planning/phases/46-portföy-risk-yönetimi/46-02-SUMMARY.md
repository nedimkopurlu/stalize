---
phase: 46-portföy-risk-yönetimi
plan: "02"
subsystem: frontend/portfolio
tags: [risk, portfolio, concentration-alerts, ui, warning]
dependency_graph:
  requires: [46-01]
  provides: [concentrationAlerts-useMemo, riskAlerts-section, riskAlerts-CSS]
  affects: [frontend/src/app/portfolio/page.tsx, frontend/src/app/portfolio/page.module.css]
tech_stack:
  added: []
  patterns: [useMemo-derived-alerts, conditional-section-render, CSS-amber-warning]
key_files:
  created: []
  modified:
    - frontend/src/app/portfolio/page.tsx
    - frontend/src/app/portfolio/page.module.css
decisions:
  - "⚠ symbol embedded in alert message string rather than icon-only — matches plan spec format 'Bankacılık sektöründe yoğunlaşma: %42 ⚠ (eşik: %35)'"
  - "concentrationAlerts sorted by pct desc — highest risk shown first"
  - "Alert section hidden when concentrationAlerts.length === 0 — no empty space left"
  - "Hardcoded #f59e0b for amber color (consistent with existing accent token in CSS)"
metrics:
  duration_minutes: 2
  completed_date: "2026-05-14"
  tasks_completed: 2
  files_changed: 2
---

# Phase 46 Plan 02: Portföy Risk — Yoğunlaşma Uyarıları Summary

**One-liner:** concentrationAlerts useMemo derives sector (>35%) and single-position (>20%) threshold breaches from riskGuard; turuncu uyarı section renders above sectorDist, hidden when no alerts (RISK-02, RISK-03).

## What Was Built

### Threshold constants (Task 1)

- `SECTOR_CONCENTRATION_THRESHOLD = 35` constant added after `EMPTY_FORM` (module-level)
- `POSITION_CONCENTRATION_THRESHOLD = 20` constant added alongside

### concentrationAlerts useMemo (Task 1)

- `ConcentrationAlert` type defined inline (key, kind, label, pct, threshold, message)
- `concentrationAlerts` useMemo scans `riskGuard.sector_exposure` for `exposure_pct > 35` (RISK-02)
- Scans `riskGuard.positions` for `exposure_pct > 20` (RISK-03)
- Results sorted by `pct` descending — highest risk alert first
- Returns `[]` when `riskGuard` is null — no alerts rendered

### riskAlerts section render (Task 1)

- `{concentrationAlerts.length > 0 && ...}` guard — section completely absent from DOM when empty
- Placed between closing `</div>` of heroGrid and `<section className={styles.sectorDist}>` (RISK-01)
- Does not touch heroGrid, K/Z table, or positions section — isolated section as per D-05
- Alert message format: `Bankacılık sektöründe yoğunlaşma: %42 ⚠ (eşik: %35)` / `THYAO tek hisse ağırlığı: %25 ⚠ (eşik: %20)`

### riskAlerts CSS (Task 2)

- `.riskAlerts`: amber border (`rgba(245,158,11,0.35)`) + subtle amber background (`rgba(245,158,11,0.08)`)
- `.riskAlertsTitle`: uppercase amber label
- `.riskAlertsList`: flex column list, gap 6px, no bullet
- `.riskAlertItem`: flex row with icon + message
- `.riskAlertIcon`: 22px circular badge with amber background, renders ⚠ glyph
- `.riskAlertMessage`: flex:1, full width
- Responsive: padding/font-size reduced at max-width 600px

## Files Touched

| File | Change |
|------|--------|
| `frontend/src/app/portfolio/page.tsx` | Added threshold constants, ConcentrationAlert type, concentrationAlerts useMemo, riskAlerts section JSX |
| `frontend/src/app/portfolio/page.module.css` | Added riskAlerts, riskAlertsTitle, riskAlertsList, riskAlertItem, riskAlertIcon, riskAlertMessage CSS classes + responsive |

## Commits

| Task | Hash | Message |
|------|------|---------|
| Task 1 | 4f0aa3d | feat(46-02): concentrationAlerts useMemo + riskAlerts section render (RISK-02, RISK-03) |
| Task 2 | 0632b1a | feat(46-02): riskAlerts CSS — turuncu yoğunlaşma uyarı stili (RISK-02, RISK-03) |

## Phase 46 Closing Notes

All four RISK requirements are now complete:

| Req | Description | Plan | Status |
|-----|-------------|------|--------|
| RISK-01 | Sektör dağılımı yatay bar chart | 46-01 | ✅ Complete |
| RISK-02 | Sektör >%35 → turuncu uyarı | 46-02 | ✅ Complete |
| RISK-03 | Tek hisse >%20 → turuncu uyarı | 46-02 | ✅ Complete |
| RISK-04 | Risk özet kartı — açık pozisyon + en büyük 3 sektör | 46-01 | ✅ Complete |

Phase 46 (Portföy Risk Yönetimi) is fully complete. Next: Phase 47 — İşlem Disiplini & Günlüğü.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data wired from real `riskGuard.sector_exposure` and `riskGuard.positions` API response.

## Self-Check: PASSED

- `frontend/src/app/portfolio/page.tsx` — modified (SECTOR_CONCENTRATION_THRESHOLD=35, POSITION_CONCENTRATION_THRESHOLD=20, concentrationAlerts useMemo, riskAlerts section)
- `frontend/src/app/portfolio/page.module.css` — modified (riskAlerts, riskAlertsTitle, riskAlertItem, riskAlertIcon CSS classes)
- Commits 4f0aa3d, 0632b1a — exist in git log
- TypeScript: `npx tsc --noEmit` — 0 errors
