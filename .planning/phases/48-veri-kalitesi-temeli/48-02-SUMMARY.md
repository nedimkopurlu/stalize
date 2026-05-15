---
phase: 48-veri-kalitesi-temeli
plan: "02"
subsystem: frontend
tags: [refactor, helpers, safe-label, tech-01]
dependency_graph:
  requires: []
  provides: [TECH-01]
  affects: [stocks-list, stock-detail, model-portfolio]
tech_stack:
  added: []
  patterns: [named-export, single-source-of-truth]
key_files:
  created: []
  modified:
    - frontend/src/components/StockHelpers.tsx
    - frontend/src/app/stocks/page.tsx
    - frontend/src/app/stocks/[symbol]/page.tsx
    - frontend/src/app/model-portfolio/page.tsx
decisions:
  - "Extracted safeLabel and safeLabelTooltip verbatim from stocks/page.tsx as the canonical source; no logic changes"
  - "SAFE_LABEL_MAP and SAFE_LABEL_TOOLTIP constants colocated with the functions in StockHelpers.tsx"
metrics:
  duration: "~5 minutes"
  completed: "2026-05-15"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
---

# Phase 48 Plan 02: safeLabel / safeLabelTooltip Centralization Summary

**One-liner:** Extracted 3 copies of `safeLabel`/`safeLabelTooltip` into single named exports in `StockHelpers.tsx`; all three pages now import from the central location (TECH-01).

## What Was Done

Two tasks executed atomically:

**Task 1 — Add exports to StockHelpers.tsx**

Appended `safeLabel` and `safeLabelTooltip` as named exports to `frontend/src/components/StockHelpers.tsx` alongside the existing four format helpers. The mapping constants (`SAFE_LABEL_MAP`, `SAFE_LABEL_TOOLTIP`) were copied verbatim from `stocks/page.tsx` (confirmed as the canonical copy). No existing exports were altered.

**Task 2 — Replace inline definitions with imports across 3 pages**

- `frontend/src/app/stocks/page.tsx`: Extended existing `@/components/StockHelpers` import to include `safeLabel, safeLabelTooltip`; removed 26-line inline block (SAFE_LABEL_MAP + SAFE_LABEL_TOOLTIP + both functions).
- `frontend/src/app/stocks/[symbol]/page.tsx`: Extended existing multi-line `@/components/StockHelpers` import; removed identical 26-line block.
- `frontend/src/app/model-portfolio/page.tsx`: Added new `@/components/StockHelpers` import line (file had no prior StockHelpers import); removed 26-line inline block.

All call sites (`safeLabel(...)`, `safeLabelTooltip(...)`) were left entirely untouched.

## Verification Results

| Check | Result |
|---|---|
| `export function safeLabel` in StockHelpers.tsx | PASS |
| `export function safeLabelTooltip` in StockHelpers.tsx | PASS |
| Total named exports in StockHelpers.tsx | 7 (>= 6 required) |
| `function safeLabel` inline in stocks/page.tsx | NONE (removed) |
| `function safeLabel` inline in stocks/[symbol]/page.tsx | NONE (removed) |
| `function safeLabel` inline in model-portfolio/page.tsx | NONE (removed) |
| `npx tsc --noEmit` | EXIT 0 (no errors) |
| `npm run lint` | EXIT 0 (no errors) |

## Commits

| Hash | Message |
|---|---|
| 5bd5027 | feat(48-02): add safeLabel and safeLabelTooltip as named exports to StockHelpers.tsx |
| 11d5ec1 | refactor(48-02): replace inline safeLabel definitions with StockHelpers import in 3 pages |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — no stubs introduced or present in modified files.

## Self-Check: PASSED

- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/components/StockHelpers.tsx` — FOUND, contains both exports
- Commits 5bd5027 and 11d5ec1 — FOUND in git log
- No inline `function safeLabel(` remains in any frontend page — VERIFIED
- TypeScript build — PASSED (no output = exit 0)
- ESLint — PASSED
