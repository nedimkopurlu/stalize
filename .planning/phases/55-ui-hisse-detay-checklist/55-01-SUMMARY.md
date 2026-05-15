---
phase: 55-ui-hisse-detay-checklist
plan: 01
subsystem: frontend
tags: [ui, navigation, stock-detail, section-nav, regime]
dependency_graph:
  requires: []
  provides: [SectionNav, RegimeSection, section-anchors]
  affects: [frontend/src/app/stocks/[symbol]/page.tsx]
tech_stack:
  added: []
  patterns: [IntersectionObserver, sticky-nav, CSS-modules]
key_files:
  created: []
  modified:
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/[symbol]/page.module.css
decisions:
  - Used a thin anchor `<div id="temel" />` between dossierSection and newsDossier rather than splitting the two-column CSS grid, preserving existing layout
  - Wrapped chartSection + dossierSection together under id="teknik" div since both are semantically the technical analysis block
  - Wrapped analysisSection + bottomSection under id="ilgili-hisseler" per plan spec
metrics:
  duration: 15m
  completed: "2026-05-15T18:49:27Z"
  tasks_completed: 2
  files_changed: 2
---

# Phase 55 Plan 01: SectionNav & Section Anchors Summary

Sticky 7-anchor SectionNav added to hisse detay page with IntersectionObserver active tracking and new RegimeSection showing ADX/EMA200/ATR stats.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | SectionNav component + CSS | 953ea51 | Done |
| 2 | Section id anchors + RegimeSection | 953ea51 | Done |

## What Was Built

### SectionNav Component

Module-level `SectionNav({ activeSection })` component renders 7 anchor links as a sticky nav bar at `top: 53px` (below the existing `topNav`). `IntersectionObserver` watches each section and updates `activeSection` state when a section enters the viewport (threshold 0.2, rootMargin -60px top / -60% bottom).

Section links:
- `#hero` → "Özet"
- `#skor-ozeti` → "Skor"
- `#teknik` → "Teknik"
- `#temel` → "Temel"
- `#haberler` → "Haberler"
- `#piyasa-rejimi` → "Piyasa Rejimi"
- `#ilgili-hisseler` → "İlgili"

### Section Anchors Added

| id | Wraps |
|----|-------|
| `id="hero"` | Existing `<section className={styles.hero}>` |
| `id="skor-ozeti"` | `<div>` wrapper around breakdownSection + positionSizeSection + thesisSection |
| `id="teknik"` | `<div>` wrapper around chartSection + dossierSection |
| `id="temel"` | Thin anchor `<div id="temel" />` placed between dossierSection and newsDossier |
| `id="haberler"` | Added to existing `<section className={styles.newsDossier}>` |
| `id="piyasa-rejimi"` | `<section>` rendered by `RegimeSection` component |
| `id="ilgili-hisseler"` | `<div>` wrapper around analysisSection + bottomSection/peers |

### RegimeSection Component

Module-level `RegimeSection({ regime: MarketRegimeResponse | null })` renders null when regime is null. When present, shows a styled card with:
- Regime label (color-coded: Boğa=green, Ayı=red, Yatay=muted, Volatil=amber)
- ADX (14) stat with description
- EMA 200 stat with description
- ATR stat with description

Placed between the newsDossier and the ilgili-hisseler wrapper in the return block.

### CSS Added to page.module.css

**SectionNav classes:** `.sectionNav`, `.sectionNavLink`, `.sectionNavLinkActive`
- Sticky at `top: 53px`, horizontal flex, `overflow-x: auto`, hidden scrollbar
- Active link: accent color + 2px bottom border

**RegimeSection classes:** `.regimeSection`, `.regimeSectionCard`, `.regimeSectionTitle`, `.regimeSectionGrid`, `.regimeSectionItem`, `.regimeSectionLabel`, `.regimeSectionValue`
- 3-column grid layout, responsive to 1-column on mobile

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Design] Used thin anchor div for id="temel" instead of restructuring dossier grid**
- **Found during:** Task 2
- **Issue:** The dossierSection uses `display: grid; grid-template-columns: 1fr 1fr` with two articles. Splitting them into separate containers would break the side-by-side layout.
- **Fix:** Placed a thin `<div id="temel" />` anchor element immediately after the dossierSection. The scroll target lands at the fundamentals area without restructuring the CSS grid.
- **Files modified:** frontend/src/app/stocks/[symbol]/page.tsx
- **Commit:** 953ea51

## Verification Results

All checks passed:
- `grep -q 'SectionNav' page.tsx` — OK
- `grep -q 'id="skor-ozeti"' page.tsx` — OK
- `grep -q 'piyasa-rejimi' page.tsx` — OK
- `grep -q 'id="haberler"' page.tsx` — OK
- `grep -q 'id="hero"' page.tsx` — OK
- `grep -q 'RegimeSection' page.tsx` — OK
- `grep -q 'regime.adx' page.tsx` — OK
- `grep -q 'sectionNav' page.module.css` — OK
- `grep -q '.regimeSectionCard' page.module.css` — OK
- `npx tsc --noEmit` — No errors
- `npm run lint` — No errors

## Known Stubs

None. All data is wired to existing `regime` state (already fetched via `api.getMarketRegime()`). RegimeSection receives live data.

## Self-Check: PASSED

- `frontend/src/app/stocks/[symbol]/page.tsx` — exists, modified
- `frontend/src/app/stocks/[symbol]/page.module.css` — exists, modified
- Commit 953ea51 — confirmed in git log
