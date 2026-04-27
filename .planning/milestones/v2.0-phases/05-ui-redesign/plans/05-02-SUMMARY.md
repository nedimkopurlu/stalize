---
phase: 05-ui-redesign
plan: "05-02"
title: "BriefingCard Component + Dashboard Integration (UIUX-01)"
subsystem: frontend
tags: [component, dashboard, briefing, ui]
requirements: [UIUX-01]

dependency_graph:
  requires: [05-01]
  provides: [BriefingCard-component, briefing-first-dashboard]
  affects: [frontend/src/app/page.tsx]

tech_stack:
  added: []
  patterns: [state-machine-prop, separate-fetch-for-nullable-resource, css-modules]

key_files:
  created:
    - frontend/src/components/BriefingCard.tsx
    - frontend/src/components/BriefingCard.module.css
  modified:
    - frontend/src/app/page.tsx

decisions:
  - "Used state prop ('loading'|'not_generated'|'loaded'|'error') instead of loading+error booleans — cleaner type-safe state machine, prevents impossible states like loading=true and error=true simultaneously"
  - "Briefing fetch runs before but separate from Promise.all — 404 is not propagated to the main error state; any error defaults to not_generated to avoid showing error UI for expected 404s"
  - "notable_stocks rendered as Link chips using direction field (up/down) for color coding — no daily_change_pct on BriefingData.notable_stocks so prompt's version was corrected to match actual API type"
  - "KAP summary is collapsible by default (kapExpanded=false) to keep the card compact"

metrics:
  duration_minutes: 20
  completed_date: "2026-04-18"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 05 Plan 02: BriefingCard Component + Dashboard Integration Summary

BriefingCard component with four-state UI (loading skeleton, not_generated empty state, error fallback, loaded rich view) wired as the first content element on the dashboard above the stats grid.

## What Was Built

### BriefingCard.tsx

Props interface:
```typescript
interface BriefingCardProps {
  briefing: BriefingData | null;
  state: 'loading' | 'not_generated' | 'loaded' | 'error';
}
```

State rendering:
- `loading` — skeleton shimmer (3 lines with animation)
- `not_generated` — clock SVG icon + Turkish message "Sabah brifing henüz üretilmedi" + schedule hint
- `error` — falls through to not_generated treatment (both show empty state)
- `loaded` — full card with: header (SABAH BRIFİNG badge + formatted date + generation time), risk_summary section, market_outlook section, price_summary section, notable_stocks chips (up to 6, colored by direction), kap_summary (collapsible toggle)

### BriefingCard.module.css

CSS classes: `.briefingCard`, `.cardHeader`, `.headerLeft`, `.briefingBadge`, `.briefingDate`, `.genTime`, `.section`, `.sectionLabel`, `.sectionText`, `.kapText`, `.collapseToggle`, `.collapseIcon`, `.notableList`, `.notableChip`, `.chipUp`, `.chipDown`, `.emptyState`, `.emptyIcon`, `.emptyTitle`, `.emptyHint`, `.skeletonLine`

All styles use existing CSS variable tokens: `--accent-cyan`, `--text-primary`, `--text-secondary`, `--text-muted`, `--border-primary`, `--bg-secondary`, `--color-positive`, `--color-negative`.

### page.tsx Changes

Insertion point: immediately after `</div>` closing the `.pageHeader` block and before `{/* ── Stats Cards ── */}`.

State variables added:
```typescript
const [briefing, setBriefing] = useState<BriefingData | null>(null);
const [briefingState, setBriefingState] = useState<'loading' | 'not_generated' | 'loaded' | 'error'>('loading');
```

Fetch pattern (at start of `loadData()`, before the main `Promise.all`):
```typescript
setBriefingState('loading');
try {
  const b = await api.getBriefing();
  setBriefing(b);
  setBriefingState('loaded');
} catch (err) {
  setBriefingState('not_generated'); // 404 and errors both show empty state
}
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected notable_stocks type mismatch in prompt**
- Found during: Task 1
- Issue: The prompt's version used `s.daily_change_pct` on notable_stocks chips, but `BriefingData.notable_stocks` type is `Array<{ symbol: string; reason?: string; direction?: string }>` — no `daily_change_pct` field exists
- Fix: Used the plan document's version which uses `s.direction` ('up'/'down') for chip color, matching the actual interface
- Files modified: BriefingCard.tsx

**2. [Rule 2 - Missing] Escaped apostrophe in JSX**
- Found during: Task 1
- Issue: "06:30'da" contains an unescaped apostrophe in JSX which would cause a React warning
- Fix: Used `&apos;` entity in the emptyHint paragraph
- Files modified: BriefingCard.tsx

## Known Stubs

None. The BriefingCard wires directly to `api.getBriefing()` which calls `/api/briefing/today`. When the backend returns a valid BriefingData object, all fields are displayed. When no briefing exists (404), the empty state is shown. No hardcoded placeholder data flows to UI rendering.

## Self-Check: PASSED

- [x] frontend/src/components/BriefingCard.tsx — FOUND
- [x] frontend/src/components/BriefingCard.module.css — FOUND
- [x] Commit 35714922 — feat(05-02): create BriefingCard component
- [x] Commit ae68e8a7 — feat(05-02): wire BriefingCard as first element in dashboard
- [x] `npm run build` exits 0, TypeScript clean
- [x] `grep "BriefingCard" page.tsx` — import on line 9, render on line 123
- [x] `grep "briefingState" page.tsx` — state declaration and setter present
