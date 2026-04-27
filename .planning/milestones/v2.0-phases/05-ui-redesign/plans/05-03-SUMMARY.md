---
phase: 05-ui-redesign
plan: "05-03"
subsystem: frontend-components
tags: [macro, dashboard, ui, indicators]
dependency_graph:
  requires: [05-01, 05-02]
  provides: [MacroPanel component, macro indicators on dashboard]
  affects: [frontend/src/app/page.tsx]
tech_stack:
  added: []
  patterns: [fire-and-forget fetch, props-based component with INDICATOR_CONFIG array, CSS Module skeleton animation]
key_files:
  created:
    - frontend/src/components/MacroPanel.tsx
    - frontend/src/components/MacroPanel.module.css
  modified:
    - frontend/src/app/page.tsx
decisions:
  - "Props-based (not self-fetching) MacroPanel — parent page.tsx owns the fetch so macro failure never blocks dashboard load"
  - "INDICATOR_CONFIG array drives all five indicators declaratively — easy to extend with new indicators"
  - "fire-and-forget fetch pattern: api.getMacroIndicators() runs outside main Promise.all so a macro endpoint outage does not block stock data"
metrics:
  duration_minutes: 20
  completed: "2026-04-17T23:58:44Z"
  tasks_completed: 2
  files_changed: 3
requirements: [UIUX-04]
---

# Phase 05 Plan 03: MacroPanel Component + Dashboard Integration Summary

MacroPanel renders five Turkish market indicators (USD/TRY, Altin TRY/g, BIST100, Faiz %, Enflasyon %) as a horizontal row of cards on the dashboard, wired between BriefingCard and Stats Cards.

## What Was Built

### MacroPanel.tsx

Props-based functional component:

```typescript
interface MacroPanelProps {
  indicators: MacroIndicators | null;
  loading: boolean;
}
```

Key design: `INDICATOR_CONFIG` array (5 entries) drives all indicator rendering. Each config entry has:
- `key: keyof MacroIndicators` — typed field key
- `label: string` — display label
- `format: (v: number) => string` — value formatter
- `positiveWhenUp: boolean` — semantic direction (reserved for future trend arrows)

Null-safe value rendering: `value !== null ? cfg.format(value) : '\u2014'` — no NaN or undefined can reach the DOM.

Three render states:
1. `loading=true` — 5 skeleton placeholder cards with shimmer animation
2. `indicators=null` (after load failed) — single error note row
3. Normal — 5 indicator cards + asOf timestamp

### MacroPanel.module.css

Scoped CSS with:
- `.macroPanel` — `display: flex; flex-wrap: wrap; gap: 12px`
- `.indicatorCard` — `flex: 1 1 140px; min-width: 120px` pill cards
- `.skeleton` — shimmer keyframe animation (1.5s ease-in-out)
- `@media (max-width: 640px)` — 2-column fallback (`flex: 1 1 calc(50% - 6px)`)
- CSS variable tokens from globals.css: `--bg-card`, `--border-primary`, `--text-muted`, `--text-primary`

### page.tsx Integration

Three targeted additions only (no existing sections removed or reordered):

1. **Import** — `import type { MacroIndicators } from '@/lib/api'` and `import MacroPanel from '@/components/MacroPanel'`
2. **State** — `macroIndicators: MacroIndicators | null` and `macroLoading: boolean`
3. **Fetch** — fire-and-forget inside `loadData()`, runs after the briefing fetch block:
   ```typescript
   setMacroLoading(true);
   api.getMacroIndicators()
     .then(setMacroIndicators)
     .catch(() => setMacroIndicators(null))
     .finally(() => setMacroLoading(false));
   ```
4. **JSX** — `<MacroPanel indicators={macroIndicators} loading={macroLoading} />` between BriefingCard and Stats Cards

Render order in `<main>`:
1. Page header
2. `<BriefingCard>` (Wave 2 / 05-02)
3. `<MacroPanel>` (this plan)
4. Stats grid
5. Top buy/sell
6. Gainers/losers
7. Intelligence grid
8. Full stock table

## Verification

- `npm run build` exits 0 — 12/12 static pages generated cleanly
- `npx tsc --noEmit` — no errors
- `grep -c "MacroPanel" frontend/src/app/page.tsx` — 3 matches (import type, import component, JSX usage)
- `grep "macroIndicators\|macroLoading" frontend/src/app/page.tsx` — 3 matches (2 state declarations + JSX usage)

## Commits

- `37c6fc21` — `feat(05-03): create MacroPanel component with CSS module`
- `28072f84` — `feat(05-03): wire MacroPanel into dashboard page.tsx`

## Deviations from Plan

None — plan executed exactly as written. Wave 2 (05-02) had already committed BriefingCard to page.tsx before this agent ran, so the targeted edit landed in the correct position without conflict.

## Known Stubs

None. MacroPanel renders real data from `/api/macro/indicators`. Null values show `—` (em dash). No hardcoded placeholders.

## Self-Check: PASSED

- [x] `frontend/src/components/MacroPanel.tsx` exists
- [x] `frontend/src/components/MacroPanel.module.css` exists
- [x] `frontend/src/app/page.tsx` has MacroPanel import and usage
- [x] Both commits exist in git log
