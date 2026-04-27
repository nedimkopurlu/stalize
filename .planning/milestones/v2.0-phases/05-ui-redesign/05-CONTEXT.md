# Phase 5: UI Redesign - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesign four frontend surfaces: dashboard (briefing card dominant), stock detail (candlestick + 3-layer scores), score table (filterable by score/recommendation), and macro panel (single-view indicators). No new backend features except one small macro indicators endpoint. No auth, no new pages beyond scope.

Requirements in scope: UIUX-01, UIUX-02, UIUX-03, UIUX-04.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

UI phase — layout/styling choices at Claude's discretion. Key constraints from research:

**UIUX-01 — Dashboard briefing card:**
- `GET /api/briefing/today` returns briefing or 404 — handle both states
- Add `getBriefing()` to `frontend/src/lib/api.ts` with `BriefingData` type
- Briefing card is dominant/first element on dashboard; existing IntelligenceOverview and top stocks table remain below it as secondary content
- "Not yet generated" state: clear Turkish message + scheduled time hint ("Her hafta içi 06:30'da üretilir")
- Briefing card sections: ai_commentary.risk_summary, notable_stocks list, kap_summary preview

**UIUX-02 — Stock detail page:**
- `lightweight-charts` v5.1.0 already installed — use `chart.addSeries(CandlestickSeries, options)` (NOT deprecated `addCandlestickSeries`)
- Data: `GET /api/stocks/{symbol}/prices` → `{time, open, high, low, close}` shape
- 3-layer scores: `technical_score`, `fundamental_score`, `sentiment_score` from `GET /api/stocks/{symbol}` — render as 3 labelled progress bars (Teknik / Temel / Algı)
- AI justification: render `GET /api/stocks/{symbol}/technical` top 3 signals as "Teknik Özet" — label accurately (not "AI Yorumu" since there's no per-stock LLM call at detail time)
- Existing stock detail page is `/app/stocks/[symbol]/page.tsx` — modify in place

**UIUX-03 — Score table:**
- Existing `/app/stocks/page.tsx` already has recommendation filter (AL/SAT/TUT) — KEEP it
- Add score range filter: two number inputs (min/max overall_score 0–100) — frontend-only filtering of existing data
- Sort by `overall_score` descending (already default) — ensure it's stable
- Show: symbol, overall_score, recommendation badge, technical_score, fundamental_score, sentiment_score, daily_change_pct

**UIUX-04 — Macro panel:**
- Add backend endpoint: `GET /api/macro/indicators` → `{usdtry, gold_try, bist100, interest_rate, inflation_rate, as_of}`
- `MacroNewsCollector` already fetches `TRY=X`, `GC=F`, `XU100.IS` via yfinance — reuse that data
- Interest rate: read from `settings.TCMB_POLICY_RATE` or last value in DB; inflation: config constant
- Frontend: new `MacroPanel` component embedded in dashboard below briefing card (no separate page — "single view, no navigation")
- Show: USD/TRY, Altın (TRY), BIST100, Faiz %, Enflasyon %

Implementation notes:
- CSS: existing CSS modules pattern (`*.module.css`) — no Tailwind, no new CSS framework
- Component file: new `frontend/src/components/BriefingCard.tsx` and `frontend/src/components/MacroPanel.tsx`
- Do NOT remove existing components (Sidebar, ScoreRing, RecommendationBadge) — they are reused
- Backend: add `GET /api/macro/indicators` in `backend/app/api/macro.py` — ~30 lines

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/lib/api.ts` — add `getBriefing()`, `getMacroIndicators()` functions + types
- `frontend/src/components/ScoreRing.tsx` — reuse for overall_score display
- `frontend/src/components/RecommendationBadge` — reuse in score table
- `frontend/src/app/globals.css` + `page.module.css` — CSS variables already defined
- `lightweight-charts` v5.1.0 — installed, use `addSeries(CandlestickSeries, opts)` (v5 API)
- `backend/app/api/macro.py` — add `/indicators` endpoint here

### Established Patterns
- Next.js `'use client'` + `useState`/`useEffect` for data fetching
- CSS modules for component-scoped styles
- `api.ts` functions all hit `http://localhost:8000/api/...`
- Stock detail at `/stocks/[symbol]` with existing price chart (Canvas 2D — replace with lightweight-charts)

### Integration Points
- `app/page.tsx` → add `getBriefing()` call + render `<BriefingCard>` and `<MacroPanel>`
- `app/stocks/[symbol]/page.tsx` → replace Canvas chart with lightweight-charts candlestick
- `app/stocks/page.tsx` → add score range filter inputs
- `backend/app/api/macro.py` → new `GET /indicators` endpoint

</code_context>

<specifics>
## Specific Ideas

- Briefing card: collapsible sections for KAP summary (long text) — default collapsed, click to expand
- Score table filter UX: inline inputs above table, instant filtering on change (no submit button)
- Candlestick chart: dark theme matching existing app dark mode; height 300px
- MacroPanel: horizontal pill/card layout — each indicator is a small card with label + value + trend arrow
- "Brifing henüz üretilmedi" state: show a clock icon + next generation time estimate

</specifics>

<deferred>
## Deferred Ideas

- Real-time price WebSocket (polling is fine for v1)
- Chat UI (CHAT-01..04 are v2 requirements)
- Per-stock LLM analysis on demand (v2)
- Historical macro charts (v2)

</deferred>

---

*Phase: 05-ui-redesign*
*Context gathered: 2026-04-18*
