---
phase: 05-ui-redesign
plan: 05-01
title: "Backend Macro Endpoint + API Types"
subsystem: backend-api, frontend-client
tags: [macro, yfinance, typescript, api-types]
requirements: [UIUX-04, UIUX-01]
dependency_graph:
  requires: [05-00]
  provides: [GET /api/macro/indicators, BriefingData, MacroIndicators, getBriefing, getMacroIndicators]
  affects: [05-02-briefing-card, 05-03-macro-panel]
tech_stack:
  added: []
  patterns: [yfinance batch download, module-level TTL cache, apiFetch generic wrapper]
key_files:
  modified:
    - backend/app/api/macro.py
    - frontend/src/lib/api.ts
decisions:
  - "Use yf.download() batch call (single network roundtrip) instead of per-ticker yf.Ticker().history()"
  - "Static TCMB/TUIK constants (42.5% rate, 38.1% inflation) — no live scraping needed for Phase 5"
  - "Gold conversion: USD/oz → TRY/gram via (gold_usd * usdtry / 31.1035)"
  - "60s module-level dict cache avoids hammering yfinance on every dashboard load"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-18"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 2
---

# Phase 5 Plan 01: Backend Macro Endpoint + API Types Summary

**One-liner:** Live `GET /api/macro/indicators` endpoint (yfinance batch fetch, 60s cache, TRY-converted gold) + `BriefingData`/`MacroIndicators` TypeScript types and `getBriefing`/`getMacroIndicators` API functions.

## What Was Built

### Task 1 — `GET /api/macro/indicators` (backend/app/api/macro.py)

New FastAPI route appended to the existing macro router. Key implementation details:

- **Route:** `@router.get("/macro/indicators")` → async function `get_macro_indicators()`
- **Cache:** Module-level `_indicators_cache` dict with 60-second TTL (`time.time()` comparison)
- **Data fetch:** `yf.download(["TRY=X", "GC=F", "XU100.IS"], period="2d", interval="1d", progress=False, auto_adjust=True)` — single batch call
- **Gold conversion:** `gold_usd * usdtry / 31.1035` (USD/oz → TRY/gram)
- **Static constants:** `interest_rate = 42.5`, `inflation_rate = 38.1` (TCMB/TUIK April 2026)
- **Error handling:** Returns HTTP 503 with Turkish detail message on total failure; individual field falls back to `None` via `last_close()` try/except

Response shape:
```json
{
  "usdtry": 38.1234,
  "gold_try": 4521.87,
  "bist100": 9876.54,
  "interest_rate": 42.5,
  "inflation_rate": 38.1,
  "as_of": "2026-04-18T10:00:00"
}
```

### Task 2 — Types + API functions (frontend/src/lib/api.ts)

Two additions made to api.ts without touching existing code:

**Types added** (inserted before `// ── API Functions ──` comment):

```typescript
export interface BriefingData {
  date: string;
  kap_summary: string | null;
  price_summary: string | null;
  macro_summary: string | null;
  notable_stocks: Array<{ symbol: string; reason?: string; direction?: string }> | null;
  ai_commentary: {
    risk_summary?: string | null;
    market_outlook?: string | null;
    [key: string]: unknown;
  } | null;
  created_at: string | null;
  generation_duration_ms: number | null;
}

export interface MacroIndicators {
  usdtry: number | null;
  gold_try: number | null;
  bist100: number | null;
  interest_rate: number | null;
  inflation_rate: number | null;
  as_of: string;
}
```

**API functions added** (appended inside `api` object, after `getLowCorrelationPairs`):

```typescript
getBriefing: () => apiFetch<BriefingData>('/briefing/today'),
getMacroIndicators: () => apiFetch<MacroIndicators>('/macro/indicators'),
```

## Commits

| Task | Hash | Message |
|------|------|---------|
| 1 | `ee80926e` | feat(05-01): add GET /api/macro/indicators endpoint to macro.py |
| 2 | `1818a7bd` | feat(05-01): add BriefingData, MacroIndicators types + getBriefing/getMacroIndicators to api.ts |

## Verification

- Python AST parse: PASS (`syntax OK`)
- `npm run build`: PASS (`Compiled successfully`, 0 TypeScript errors, 12 static pages generated)
- `grep` checks: all 4 identifiers (`getBriefing`, `getMacroIndicators`, `BriefingData`, `MacroIndicators`) confirmed in api.ts

## Deviations from Plan

None — plan executed exactly as written. The plan already specified the precise implementation (yf.download batch, cache dict, static constants). Used the plan's implementation verbatim.

## Known Stubs

None. Both additions are fully wired:
- Backend endpoint fetches live data from yfinance
- Frontend functions call real API endpoints via `apiFetch`

## Self-Check: PASSED

- `backend/app/api/macro.py` — modified, syntax OK
- `frontend/src/lib/api.ts` — modified, TypeScript build clean
- Commits `ee80926e` and `1818a7bd` exist on `main`
