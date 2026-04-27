---
phase: 05-ui-redesign
plan_id: 05-00
title: "Phase Validation Baseline"
requirements: []
wave: 0
estimated_minutes: 10
autonomous: true
depends_on: []
files_modified:
  - .planning/phases/05-ui-redesign/VALIDATION.md
must_haves:
  truths:
    - "VALIDATION.md exists and documents the automated gate for every phase requirement"
    - "Build command is documented and known to pass before any wave-1 work begins"
  artifacts:
    - path: ".planning/phases/05-ui-redesign/VALIDATION.md"
      provides: "Per-requirement validation strategy for the executor"
  key_links: []
---

<objective>
Create the VALIDATION.md baseline document for Phase 5. This phase has no frontend test framework, so the automated gate is TypeScript compilation + lint. VALIDATION.md records what to run after each wave and what manual browser smoke tests confirm each requirement.

Purpose: Give every executor a single reference for "how do I know this task is done?"
Output: .planning/phases/05-ui-redesign/VALIDATION.md
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write VALIDATION.md</name>
  <files>.planning/phases/05-ui-redesign/VALIDATION.md</files>
  <action>
Create `.planning/phases/05-ui-redesign/VALIDATION.md` with the following content:

```markdown
# Phase 05 — UI Redesign: Validation Strategy

## Automated Gate

No frontend test framework exists. TypeScript compilation + lint serve as the compile-time gate.

**Per-task command (run after every task that touches frontend):**
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build
```

**Per-wave command (run before moving to the next wave):**
```
cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run lint && npm run build
```

Build must exit 0. Any TypeScript error or lint error is a blocker.

**Backend validation (Wave 1 only):**
```
curl -s http://localhost:8000/api/macro/indicators | python3 -m json.tool
```
Must return JSON with keys: usdtry, gold_try, bist100, interest_rate, inflation_rate, as_of.

---

## Per-Requirement Smoke Tests

### UIUX-01 — Dashboard Briefing Card
- Open http://localhost:3000 in browser
- If briefing not yet generated: page shows "Sabah brifing henüz üretilmedi" with next-generation time hint — NOT an error state
- If briefing exists: BriefingCard is the first visible element, shows risk_summary, notable_stocks list, kap_summary (collapsed by default)
- MacroPanel and existing stock table appear below BriefingCard

### UIUX-02 — Stock Detail Candlestick + Scores
- Open http://localhost:3000/stocks/THYAO (or any valid symbol)
- Candlestick chart renders (green/red candles, not a flat line)
- Three score rings visible: Temel, Teknik, Algı — each with a numeric label
- "Teknik Özet" section shows top 3 signals as structured text (not blank)
- No JavaScript console errors on mount or unmount

### UIUX-03 — Score Table Filter
- Open http://localhost:3000/stocks
- "Min Skor" and "Max Skor" number inputs are visible in the filter bar
- Typing 70 in Min Skor removes stocks with overall_score < 70 instantly (no submit button needed)
- Existing recommendation filter (AL/SAT/TUT) still works alongside score range filter
- Filters compose: both active at same time narrows results correctly

### UIUX-04 — Macro Panel
- Open http://localhost:3000 (dashboard)
- MacroPanel renders below BriefingCard: shows USD/TRY, Altın, BIST100, Faiz %, Enflasyon % as horizontal cards
- Each card has a label, a numeric value, and a trend indicator
- No "undefined" or "NaN" visible in any card value

---

## Wave Gate Summary

| Wave | Gate |
|------|------|
| 0 | This file exists |
| 1 | `npm run build` passes; `curl /api/macro/indicators` returns valid JSON |
| 2 | `npm run build` passes; UIUX-01 smoke test passes |
| 3 | `npm run build` passes; UIUX-04 smoke test passes |
| 4 | `npm run build` passes; UIUX-02 smoke test passes |
| 5 | `npm run lint && npm run build` passes; UIUX-03 smoke test passes; human checkpoint approved |
```
  </action>
  <verify>
    <automated>ls /Users/nedimkopurlu/Downloads/PROJELER/stalize/.planning/phases/05-ui-redesign/VALIDATION.md</automated>
  </verify>
  <done>VALIDATION.md exists with automated gate commands and per-requirement smoke test steps for all four UIUX requirements.</done>
</task>

</tasks>

<verification>
File exists at the expected path. Content reviewed manually by executor before moving to wave 1.
</verification>

<success_criteria>
VALIDATION.md created. Each executor in waves 1–5 has a clear reference for what "done" means per requirement.
</success_criteria>

<output>
After completion, create `.planning/phases/05-ui-redesign/plans/05-00-SUMMARY.md` documenting that VALIDATION.md was created.
</output>
