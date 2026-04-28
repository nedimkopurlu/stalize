# Phases 19–21 Summary

**Completed:** 2026-04-28

## Phase 19: UI/UX Foundation

- **ThemeToggle**: Now detects `prefers-color-scheme` on first load (no localStorage → system preference wins); manual override persists
- **Sidebar nav**: Added Tarama (screener) and İzleme Listesi (watchlist) items (08, 09)
- **Branding**: "BIST100 Analiz" → "BIST Analiz Terminali"; layout metadata updated for full BIST universe
- **Status text**: Updated to reflect new features (tarama, model portföy, kişisel takip)

Files: `ThemeToggle.tsx`, `Sidebar.tsx`, `layout.tsx`

## Phase 20: Tarama Motoru (Screener)

**Backend:**
- New `/screener` endpoint in `backend/app/api/stocks.py`
- Filters: sector, bist30/100/250, score range, recommendation, market_cap range, daily_change range, pe_ratio, pb_ratio, roe, debt_to_equity
- Two-step approach: SQL filters on Stock table → batch Fundamental fetch → Python post-filter
- Returns: count + stocks array with all key metrics

**Frontend:**
- New page at `frontend/src/app/screener/page.tsx`
- 4 template presets: Düşük F/K, Momentum, Güçlü Bilanço, Yüksek Temettü
- Filter form: sector, score, pe_ratio, pb_ratio, roe, recommendation, sort_by + BIST index toggles
- LocalStorage filter set save/load
- Results table: symbol, price, change, sector, score, F/K, PD/DD, ROE, sinyal

## Phase 21: Watchlist + Portföy

**Frontend (localStorage-based, no backend needed):**
- New page at `frontend/src/app/watchlist/page.tsx`
  - Add/remove symbols via input or button
  - Loads live data for all watched symbols via `api.getStocks({ limit: 500 })`
  - Displays: price, change, sector, score ring, recommendation
  - Empty state, skeleton loading, "not found" count
- Stock detail page (`/stocks/[symbol]/page.tsx`):
  - "☆ İzlemeye Ekle" / "★ İzlemede" toggle button in page header
  - Reads/writes `stalize-watchlist` localStorage key

Storage key: `stalize-watchlist` (array of symbol strings)
