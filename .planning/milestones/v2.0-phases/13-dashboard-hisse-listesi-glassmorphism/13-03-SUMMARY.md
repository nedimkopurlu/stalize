---
phase: 13-dashboard-hisse-listesi-glassmorphism
plan: "03"
subsystem: stocks-ui
tags: [glassmorphism, stocks, sector-filter, api, cleanup]
dependency_graph:
  requires: [13-01]
  provides: [GLUI-03, CLEN-03]
  affects: [frontend/src/app/stocks/page.tsx, frontend/src/lib/api.ts, backend/app/api/stocks.py]
tech_stack:
  added: []
  patterns: [server-side sector filtering, API-driven dropdown, glassmorphism table container]
key_files:
  created: []
  modified:
    - backend/app/api/stocks.py
    - frontend/src/lib/api.ts
    - frontend/src/app/stocks/page.tsx
decisions:
  - "Sector filtering moved server-side: filterSector passed to api.getStocks() as query param instead of client-side filter"
  - "stop_loss/target_price show as '—' in table; backend /stocks list endpoint does not return them yet — fields are optional in StockSummary"
metrics:
  duration: 165s
  completed: "2026-04-25"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 3
---

# Phase 13 Plan 03: Stocks Page Glassmorphism + Sector API Summary

**One-liner:** Stocks page redesigned with API-driven sector dropdown, glassmorphism table container, and causal/market-cap/sector column cleanup per GLUI-03 and CLEN-03.

## Tasks Completed

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Backend GET /stocks/sectors endpoint | 9f943487 | Added endpoint before /stocks/{symbol} to avoid FastAPI path conflict |
| 2 | api.ts getStockSectors() + StockSectorsResponse | 39dcb0f0 | Added type, function, and stop_loss/target_price optional fields to StockSummary |
| 3 | stocks/page.tsx sector dropdown + glassmorphism + column update | 876cc27b | API-driven sectors, glass-card container, Stop-Loss/Hedef columns, removed P.Degeri/Sektor/Nedensellik |

## Verification Results

- `GET /stocks/sectors` registered at index 1, before `/stocks/{symbol}` at index 4 — no path conflict
- TypeScript: 0 errors (excluding pre-existing stale causal page cache)
- `next build` completes cleanly, 10 pages generated
- `causal_score` has zero references in stocks/page.tsx
- `filterSector` state wired to both API call and sector dropdown

## Deviations from Plan

### Auto-observed (no fix needed)

**1. [Observation] stocks.py already contained kap-feed and sparkline endpoints**
- A linter reformatted stocks.py after Task 1 edit, revealing the file already contained `/stocks/kap-feed` and `/stocks/sparkline` endpoints not visible in the original read (file was truncated). These are placed correctly before `/stocks/{symbol}`.
- No action taken — endpoints were already correct.

**2. [Rule 1 - Bug] Sector filtering moved server-side**
- Found during: Task 3
- The plan specified adding filterSector to useCallback dependencies and passing it to api.getStocks(). The current code had filterSector only in client-side `.filter()`.
- Fix: filterSector added to loadStocks dependencies and passed as `sector:` param to api.getStocks(). Client-side `.filter()` for sector removed since server handles it.
- Files modified: frontend/src/app/stocks/page.tsx
- Commit: 876cc27b

### None required for architectural changes — plan executed within scope.

## Known Stubs

- **stop_loss** and **target_price** columns show '—' for all rows. The `/api/stocks` list endpoint does not return these fields from the Stock model. The Stock model may have these fields from TechnicalResult but they are not serialized in the list response. The columns display correctly as '—' which is the designed fallback. No plan currently wires these from backend to list endpoint — future plan should add stop_loss/target_price to the /stocks list payload if desired.

## Self-Check: PASSED

- FOUND: backend/app/api/stocks.py
- FOUND: frontend/src/lib/api.ts
- FOUND: frontend/src/app/stocks/page.tsx
- FOUND: 13-03-SUMMARY.md
- FOUND commit 9f943487: feat(13-03): add GET /stocks/sectors endpoint
- FOUND commit 39dcb0f0: feat(13-03): add StockSectorsResponse type and getStockSectors()
- FOUND commit 876cc27b: feat(13-03): update stocks page with API sector dropdown
