---
phase: 34
slug: frontend-tasar-m-d-zeltmeleri
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-05-08
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript strict mode (no frontend test suite) |
| **Config file** | `frontend/tsconfig.json` (strict: true) |
| **Quick run command** | `cd frontend && npx tsc --noEmit` |
| **Full suite command** | `cd frontend && npx tsc --noEmit && npx next build` |
| **Estimated runtime** | ~15 seconds (tsc) / ~60 seconds (full build) |

---

## Sampling Rate

- **After every task commit:** `cd frontend && npx tsc --noEmit`
- **After every plan wave:** `cd frontend && npx tsc --noEmit && npx next build`
- **Before `/gsd:verify-work`:** Full build must be green + manual visual check in both light and dark mode
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 34-01-T1 | 34-01 | 1 | DESIGN-01 | TypeScript | `cd frontend && npx tsc --noEmit` | ✅ tsconfig.json | ⬜ pending |
| 34-01-T2 | 34-01 | 1 | DESIGN-02 | TypeScript | `cd frontend && npx tsc --noEmit` | ✅ tsconfig.json | ⬜ pending |
| 34-02-T1 | 34-02 | 2 | DESIGN-03 | TypeScript | `cd frontend && npx tsc --noEmit` | ✅ tsconfig.json | ⬜ pending |
| 34-02-T2 | 34-02 | 2 | DESIGN-04, DESIGN-06 | TypeScript + Manual | `cd frontend && npx tsc --noEmit` | ✅ tsconfig.json | ⬜ pending |
| 34-02-T3 | 34-02 | 2 | DESIGN-05 | TypeScript | `cd frontend && npx tsc --noEmit` | ✅ tsconfig.json | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — no new test files needed. TypeScript strict mode via `frontend/tsconfig.json` is the automated gate for all structural changes.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Light mode hover visible | DESIGN-04 | CSS visual — TypeScript cannot verify color rendering | Open app in light mode, hover a stock row, confirm background changes to `#f4f4f5` (not invisible) |
| Dark mode hover unchanged | DESIGN-04 | CSS visual regression | Open app in dark mode, hover a stock row, confirm hover effect still visible |
| 1G/1H mock chart looks plausible | DESIGN-01 | Chart rendering — TypeScript cannot verify SVG output | Select 1G tab, confirm chart renders with ~48 data points; select 1H, confirm ~30 points |
| Strategy cards readable | DESIGN-03 | Visual layout check | Open /model-portfolio, confirm 6 cards visible with title + description |
| Portfolio empty state CTA | DESIGN-06 | End-to-end flow | Remove all portfolio positions, open dashboard, confirm "Henüz portföy eklenmedi" + link to /portföy visible |
