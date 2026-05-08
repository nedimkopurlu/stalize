---
phase: "36"
plan: "36-01"
title: "Hisse Detay + Gemini Analizi"
subsystem: "stocks-detail-ai"
tags: [backend, frontend, ai, gemini, tdd, tooltips]
dependency_graph:
  requires: []
  provides:
    - POST /stocks/{symbol}/analyze endpoint
    - StockAnalysisResponse TypeScript interface
    - analyzeStock API method
    - Analiz Et UI button + analysis panel
    - Fundamental metric Turkish tooltips
  affects:
    - frontend/src/app/stocks/[symbol]/page.tsx
    - backend/app/api/stocks.py
tech_stack:
  added:
    - gemini_service.generate() integration in stocks router
  patterns:
    - TDD (RED → GREEN with mocked gemini_service)
    - Session-scoped client-side analysis cache (LLM-02)
    - Native browser title= tooltip (no CSS complexity)
key_files:
  created:
    - path: backend/tests/test_stocks_analyze.py
      lines: "1-55"
      note: "4 tests covering shape, 404, fallback, ISO8601"
  modified:
    - path: backend/app/api/stocks.py
      lines: "421-472"
      note: "Added gemini_service import + analyze_stock endpoint"
    - path: frontend/src/lib/api.ts
      lines: "574-583"
      note: "StockAnalysisResponse interface + analyzeStock method"
    - path: frontend/src/app/stocks/[symbol]/page.tsx
      lines: "14-21 (imports), 148-150 (state), 163-177 (handleAnalyze), 423-435 (button+panel), 529-568 (tooltips)"
      note: "Full Analiz Et UI + tooltip title attributes"
    - path: frontend/src/app/stocks/[symbol]/page.module.css
      lines: "713-749"
      note: "analyzeBtn, analyzePanel, analyzeText CSS classes"
decisions:
  - "POST method for analyze endpoint (not idempotent — every call hits Gemini)"
  - "Frontend session-scoped cache via analysis !== null guard (LLM-02 compliance)"
  - "Native browser title= tooltip — no additional CSS module complexity needed"
  - "gemini_service never raises — FALLBACK_MESSAGE ensures 200 even on API failure"
  - "Prompt includes sector, price, daily change, scores, recommendation, F/K, PD/DD, ROE"
metrics:
  duration: "~25 minutes"
  completed_date: "2026-05-08"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 5
  files_created: 1
---

# Phase 36 Plan 01: Hisse Detay + Gemini Analizi Summary

**One-liner:** On-demand Türkçe Gemini analizi için POST endpoint + session-cache korumalı "Analiz Et" butonu + altı temel metrikte native browser tooltip'leri.

## What Was Implemented

### Task 1: Backend TDD — POST /stocks/{symbol}/analyze

**RED phase:** Created `backend/tests/test_stocks_analyze.py` with 4 pytest-asyncio tests:
- `test_analyze_returns_expected_shape` — 200 with correct keys/values, mocked gemini_service
- `test_analyze_nonexistent_stock_returns_404` — 404 for unknown symbol
- `test_analyze_fallback_returns_200` — 200 even when gemini returns FALLBACK_MESSAGE
- `test_analyze_generated_at_is_iso8601` — datetime.fromisoformat validation

**GREEN phase:** Added to `backend/app/api/stocks.py`:
- `from app.services.gemini_service import gemini_service` import
- `@router.post("/stocks/{symbol}/analyze")` endpoint that:
  - Looks up stock by symbol (404 if not found)
  - Fetches most recent Fundamental record for context
  - Builds Turkish prompt with sector, price, scores, recommendation, F/K, PD/DD, ROE
  - Calls `await gemini_service.generate(prompt)` — never raises, always returns text
  - Returns `{symbol, analysis, cached: False, generated_at: ISO8601}`

**Test result:** 4/4 passed.

### Task 2: Frontend API — StockAnalysisResponse + analyzeStock

Added to `frontend/src/lib/api.ts`:
- `StockAnalysisResponse` interface exported after `StockPeersResponse`
- `analyzeStock(symbol)` method in the api object after `getStockPeers` — uses `{ method: 'POST' }`
- `npx tsc --noEmit`: zero errors

### Task 3: Frontend UI — Analiz Et button, analysis panel, tooltips

Changes to `frontend/src/app/stocks/[symbol]/page.tsx`:
- Added `StockAnalysisResponse` to named imports from `@/lib/api`
- Added `analysis: string | null` and `analyzeLoading: boolean` state variables
- Added `handleAnalyze()` with LLM-02 session-cache guard: if `analysis !== null || analyzeLoading`, returns immediately — no duplicate Gemini calls
- Added Analiz Et button inside Score Card after `scoreCardRows` div:
  - Shows "✦ Analiz Et" by default, "Analiz ediliyor..." during request, "Analiz Tamamlandı" after
  - Disabled when loading or analysis already loaded
- Added `analyzePanel` + `analyzeText` rendering when `analysis !== null`
- Added `title` attributes to 6 fundamental metric `fundLabel` spans (STCK-02):
  - F/K, PD/DD, ROE, Net Marj, Borç/Özkaynak, EV/FAVÖK — all with Turkish descriptions

Added to `frontend/src/app/stocks/[symbol]/page.module.css`:
- `.analyzeBtn` — full-width, accent-soft background, accent border/color, hover/disabled states
- `.analyzePanel` — card-style container with border-primary border and bg-elevated background
- `.analyzeText` — 13px, 1.65 line-height, pre-wrap for multi-paragraph analysis text

## Test Results

| Check | Result |
|-------|--------|
| `pytest tests/test_stocks_analyze.py` | 4/4 PASSED |
| `npx tsc --noEmit` | 0 errors |

## Commits

| Hash | Message |
|------|---------|
| e4f6a37 | test(36-01): add failing tests for analyze endpoint (RED) + feat: implement POST endpoint (GREEN) |
| 23b1778 | feat(36-01): add StockAnalysisResponse type + analyzeStock API method |
| eba2af1 | feat(36-01): Analiz Et button, analysis panel, fundamental tooltips |

## Deviations from Plan

**1. [Rule 1 - Minor] Import name note:**
The plan's task 1 description mentioned using `Fundamental.symbol` for lookup, but the Fundamental model in the actual codebase uses `Fundamental.stock_id` (FK relationship). The endpoint implementation uses the correct `stock_id` join pattern matching the existing `get_stock_fundamentals` endpoint pattern.

**2. [Minor adjustment] Button text:**
Plan said `'✓ Analiz Hazır'` for the done state, CONTEXT.md and final task description said `'Analiz Tamamlandı'`. Used `'Analiz Tamamlandı'` as it is more descriptive and matches the plan's task 3 section.

Otherwise — no architectural deviations. Plan executed exactly as specified.

## Known Stubs

None — all data is wired end-to-end. The analysis result comes from live Gemini API (or FALLBACK_MESSAGE on failure). Session cache is intentional per LLM-02 requirement.

## Self-Check: PASSED
