---
phase: 55-ui-hisse-detay-checklist
plan: "02"
subsystem: frontend
tags: [modal, checklist, ux, position-sizing, risk-management]
dependency_graph:
  requires: [55-01]
  provides: [PreTradeChecklistModal, positionBtn]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [CSS-only modal, React state scroll lock, inline component with props interface]
key_files:
  created: []
  modified:
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - Used `React.useState` and `React.useEffect` inside the modal function component (React namespace already imported at top)
  - Modal renders inside editorialPage wrapper so it still sits within the AppShell DOM tree; z-index 100 ensures it overlays everything including topNav (z-index 10)
  - Checklist items 1-6 show auto-populated read-only values; item 7 (Çıkış Planı) is an editable textarea pre-filled from planStop/planTarget
  - `checklistOpen &&` guard prevents mounting the modal when closed (avoids useEffect running unnecessarily)
  - HTML entity `&#39;` used for apostrophe in JSX to satisfy ESLint react/no-unescaped-entities rule
metrics:
  duration_minutes: 15
  completed_date: "2026-05-15T18:52:54Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 55 Plan 02: PreTradeChecklistModal + Pozisyon Aç button Summary

One-liner: CSS-only 7-item pre-trade checklist modal with auto-populated regime, liquidity, score, correlation, limit-check, lot-size, and editable exit-plan fields, triggered by a "Pozisyon Aç" hero button.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | PreTradeChecklistModal component + CSS | da62ab0 | page.tsx, page.module.css |
| 2 | Pozisyon Aç button + modal integration | da62ab0 | page.tsx |

## What Was Built

### PreTradeChecklistModal Component

A module-level (non-exported) React function component defined in `frontend/src/app/stocks/[symbol]/page.tsx` with the following props interface:

```typescript
interface ChecklistModalProps {
  open: boolean;
  onClose: () => void;
  regime: MarketRegimeResponse | null;
  liquidityScore: string | null | undefined;
  overallScore: number | null | undefined;
  recommendation: string | null;
  dailyChangePct: number | null | undefined;
  positionSize: PositionSizeResponse | null;
  planStop: number | null;
  planTarget: number | null;
  symbol: string;
}
```

### 7 Checklist Items and Data Sources

| # | Label | Data Source | Special Logic |
|---|-------|-------------|---------------|
| 1 | Piyasa Rejimi | `regime?.regime` | Color-coded dot; Ayı/Volatil shows caution note |
| 2 | Likidite | `s.liquidity_score` | Red warning when `'düşük'` |
| 3 | Genel Skor | `s.overall_score` + `recommendation` | `safeLabel()` applied; note changes below/above 60 |
| 4 | Korelasyon | Static text | Manual check instruction, no backend data |
| 5 | Tavan/Taban | `s.daily_change_pct` | `Math.abs(pct) >= 9.8` → TAVAN/TABAN warning |
| 6 | Pozisyon Büyüklüğü | `positionSize.max_shares_1pct/2pct` | Falls back to static %1-2 text if null |
| 7 | Çıkış Planı | `planStop` + `planTarget` | Pre-filled editable `<textarea>` |

### Button Placement

`+ Pozisyon Aç` button added in the hero `heroLeft` column immediately after `<RegimeBadge regime={regime} />`. Uses `setChecklistOpen(true)` on click.

### CSS Classes Added to page.module.css

- `.modalBackdrop` — fixed full-screen backdrop, z-index 100, blur(4px)
- `.modalCard` — white-surface card, max-width 540px, max-height 90vh with scroll
- `.modalHeader`, `.modalTitle`, `.modalSubtitle`, `.modalCloseBtn`
- `.checklistItems`, `.checklistItem` — 7-column grid (icon | content | checkbox)
- `.checklistIcon`, `.checklistContent`, `.checklistLabel`, `.checklistValue`, `.checklistNote`, `.checklistWarning`
- `.checklistCheckbox` — accent-color styled
- `.exitPlanTextarea` — themed textarea for exit plan
- `.modalDivider`, `.modalConfirmBtn`
- `.positionBtn` — green-tinted inline-flex button for hero section
- Responsive `@media (max-width: 480px)` adjustments

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All 7 checklist items have live data sources or intentional static text (items 4 and 6 fallback). The exit plan textarea is pre-filled from actual `planStop`/`planTarget` values when available.

## Self-Check: PASSED

- `grep -q 'PreTradeChecklistModal' frontend/src/app/stocks/[symbol]/page.tsx` — FOUND
- `grep -q 'checklistOpen' frontend/src/app/stocks/[symbol]/page.tsx` — FOUND
- `grep -q 'Pozisyon Aç' frontend/src/app/stocks/[symbol]/page.tsx` — FOUND
- `grep -q 'modalBackdrop' frontend/src/app/stocks/[symbol]/page.module.css` — FOUND
- `grep -c 'checklistItem' frontend/src/app/stocks/[symbol]/page.tsx` — 8 (7 items + 1 checklistItems container class ref)
- `grep -c 'setChecklistOpen' frontend/src/app/stocks/[symbol]/page.tsx` — 3 (init, open, close)
- `npx tsc --noEmit` — exit 0
- `npm run lint` — exit 0
- Commit da62ab0 verified in git log
