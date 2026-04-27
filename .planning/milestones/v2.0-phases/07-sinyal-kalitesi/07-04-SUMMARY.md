---
phase: 07-sinyal-kalitesi
plan: "04"
subsystem: frontend
tags: [ui, types, sgnl-01, sgnl-02, sgnl-03, technical-tab, stocks-list]
dependency_graph:
  requires: [07-02, 07-03]
  provides: [frontend-sgnl-ui]
  affects: [frontend/src/lib/api.ts, frontend/src/app/stocks/[symbol]/page.tsx, frontend/src/app/stocks/page.tsx]
tech_stack:
  added: []
  patterns: [null-coalescing guard, ternary render, title tooltip, CSS variables for border color]
key_files:
  created: []
  modified:
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/stocks/page.tsx
decisions:
  - "Single-line ternary for volume_ratio guard + render — grep -c returns 1 (line count) but both guard and render present; spec intent satisfied"
  - "stop_loss/target_price block inserted as sibling after Destek/Direnc block using existing srGrid/srCard/srLabel/srValue CSS classes — no new styles needed"
  - "Auto-approved human-verify checkpoint in autonomous mode — build compiles cleanly, TypeScript 0 errors"
metrics:
  duration_seconds: 81
  completed_date: "2026-04-19"
  tasks_completed: 4
  files_modified: 3
requirements: [SGNL-01, SGNL-02, SGNL-03]
---

# Phase 07 Plan 04: Frontend UI for Phase 7 Signal Outputs Summary

**One-liner:** Surface SGNL-01/02/03 backend outputs in UI — stop-loss + target price cards on Technical tab, volume ratio with raw-volume tooltip on /stocks Hacim column, divergence signals auto-render via existing signals loop.

## What Was Built

Three frontend files updated to surface Phase 7 backend signal outputs:

1. **`frontend/src/lib/api.ts`** — Extended `StockSummary` with `volume_ratio: number | null` and `TechnicalResult` with `stop_loss: number | null` + `target_price: number | null`. TypeScript interfaces now match Phase 7 backend payloads exactly.

2. **`frontend/src/app/stocks/[symbol]/page.tsx`** — Added "Risk Levels" block below the Destek/Direnç section in the Technical tab. When `stop_loss != null`, a red-bordered card displays "Stop-Loss (2×ATR)" with formatted price. When `target_price != null`, a green-bordered card displays "Hedef Fiyat" with formatted price. Both use existing `srGrid/srCard/srLabel/srValue` CSS classes for visual consistency.

3. **`frontend/src/app/stocks/page.tsx`** — Hacim column now renders `volume_ratio.toFixed(1)x` (e.g. "2.4x") instead of raw volume. The `title` attribute on the `<td>` provides a native browser tooltip showing "Ham hacim: [formatted volume]". When `volume_ratio` is null, em-dash "—" is shown gracefully with no tooltip.

4. **Divergence signals (SGNL-03)** — No code change needed. The existing "Aktif Sinyaller" loop in `page.tsx` already renders every `signal.name` from `technical.signals[]`. RSI divergence signals added by the backend (phase 07-02) appear automatically with bullish/bearish badge.

## Verification

- `npx tsc --noEmit` — 0 errors
- `npm run build` — succeeds, all 12 pages generated

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | a5f0cb63 | feat(07-04): extend API types with stop_loss, target_price, volume_ratio |
| Task 2 | 1ca2e1ef | feat(07-04): render stop_loss and target_price on Technical tab (SGNL-01) |
| Task 3 | 9549eead | feat(07-04): render volume_ratio with tooltip on /stocks Hacim column (SGNL-02) |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Minor Acceptance Criteria Note

**Task 3:** The acceptance criterion states `grep -c "stock.volume_ratio" ... returns >= 2`. The grep `-c` flag counts matching *lines* (not occurrences). Both the null guard (`stock.volume_ratio != null`) and the render (`stock.volume_ratio.toFixed(1)`) appear on the same ternary line, so `grep -c` returns 1. However, `grep -o` confirms 2 occurrences — both guard and render are present. The intent of the criterion is satisfied. No deviation in behavior.

### Checkpoint

Task 4 (human-verify) auto-approved in autonomous mode. Build passes cleanly.

## Known Stubs

None — all three data fields are wired from API response to UI render. No placeholder text, no hardcoded empty values.

## Self-Check: PASSED
