# Phase 5: UI Redesign - Research

**Researched:** 2026-04-18
**Domain:** Next.js 16 App Router / lightweight-charts v5 / CSS Modules / TypeScript
**Confidence:** HIGH

---

## Summary

The Stalize frontend is a Next.js 16 App Router application with a dark-themed design system defined entirely in `globals.css` (CSS variables + utility classes) and per-page CSS Modules. No Tailwind or styled-components — all styling uses the existing `--css-variable` tokens and `.card`, `.badge`, `.btn`, `.data-table` global classes. The design system is well-factored and clean; the problem is page-level layout, not the token system.

The dashboard (`page.tsx`) is information-dense and unfocused. It leads with five stat cards and four "top stocks" cards — but the morning briefing (Phase 4 output) is completely absent from the UI. The stock detail page uses a hand-rolled canvas line chart (not candlestick), displays scores as six separate cards above tabs rather than in a unified view, and has no AI justification text. The score table (`/stocks`) exists and is functional but lacks score-range filtering.

The macro panel requirement (UIUX-04) has no backend endpoint for live market indicators (USD/TRY, gold, interest rate, BIST 100 index). The `GET /api/macro/events` endpoint returns KAP/TCMB/TUIK news items — not live tick data. A new backend endpoint or yfinance-backed scrape of XU100.IS / TRY=X / GC=F is required, or the panel can be composed from data already in the `MacroNewsCollector.macro_symbols` map by adding a dedicated GET route.

**Primary recommendation:** Build four new/modified components (BriefingCard, CandlestickPanel, ScoreLayerPanel, FilterableScoreTable) using existing design tokens. Use lightweight-charts v5 `createChart` + `chart.addSeries(CandlestickSeries)` for UIUX-02. Add one new backend endpoint `GET /api/macro/indicators` returning USD/TRY, gold, interest rate, BIST100 from yfinance for UIUX-04.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UIUX-01 | Dashboard redesigned as morning briefing card (dominant); "not yet generated" empty state | briefing.py returns 404 when not generated; `GET /api/briefing/today` data shape confirmed |
| UIUX-02 | Stock detail: candlestick chart + 3-layer scores (temel/teknik/algı) + AI justification in single view | `GET /api/stocks/{symbol}/prices` has OHLCV; lightweight-charts v5 CandlestickSeries available; scores on `StockDetail.stock`; AI justification field not yet in API response |
| UIUX-03 | Score table — all BIST100 ranked by overall_score, filterable by score range or AL/SAT/TUT | `/stocks` page already exists with recommendation filter; score-range filter needs frontend-only filtering on loaded data |
| UIUX-04 | Macro panel — USD/TRY, interest rate, inflation, gold, BIST100 index in single view, no navigation | No `GET /api/macro/indicators` endpoint exists; backend yfinance infrastructure present via MacroNewsCollector |
</phase_requirements>

---

## Current Frontend State

### What Exists and Works

| File | Status | Notes |
|------|--------|-------|
| `globals.css` | SOLID — do not rewrite | Complete design system: CSS vars, `.card`, `.badge`, `.btn`, `.data-table`, `.tab-bar`, `.skeleton` |
| `components/ScoreRing.tsx` | REUSABLE | SVG ring, color-coded by score, null-safe, supports `showLabel` prop |
| `components/StockHelpers.tsx` | REUSABLE | `RecommendationBadge`, `PriceChange`, `formatPrice`, `formatVolume`, `formatMarketCap`, `formatPercentage` |
| `components/Sidebar.tsx` | REUSABLE — add "Sabah Brifing" nav item | 9 nav items, active-state highlighting, fixed width 280px |
| `app/stocks/page.tsx` | WORKS — extend | Full BIST100 table with search, sort, recommendation filter, BIST30 toggle |
| `app/stocks/[symbol]/page.tsx` | MODIFY heavily | Tabs: chart / technical / causal; chart is canvas line chart |

### What Is Broken / Missing

1. **Dashboard (`page.tsx`)**: Morning briefing entirely absent. Opens with five stat cards then top-buy/sell/gainers/losers — four separate card pairs plus an intelligence feed. No dominant "briefing card" concept. The `api.getBriefing()` function does not exist in `lib/api.ts`.

2. **Stock detail chart**: Hand-rolled Canvas 2D API line chart (`renderChart` via `useEffectEvent`). Not a candlestick — only `close` prices drawn with SMA50/SMA200 overlay lines. `lightweight-charts` is installed at v5.1.0 but **not used anywhere in the codebase**.

3. **Score display on stock detail**: Six `ScoreRing` components shown as a flat `scoresGrid` row above the tabs. UIUX-02 requires temel/teknik/algı three-layer layout with AI justification text. The `fundamental_score` exists in the API but the scores are labeled inconsistently: the requirement uses temel/teknik/algı — these map to `fundamental_score` / `technical_score` / `sentiment_score`.

4. **AI justification text on stock detail**: The `StockDetail` type has no `ai_commentary` field. The briefing model has `ai_commentary` (JSON), but it is per-day/system-level, not per-stock. There is no per-stock AI text endpoint today. This field must either be derived from the technical `signals` text or left as a "Phase 6" item — **must be flagged as a gap**.

5. **Score table (`/stocks`)**: Missing score-range filter (e.g., filter stocks where `overall_score` >= 60). Current filter is recommendation string only. No score slider or numeric range inputs.

6. **Macro panel**: No page exists. No backend endpoint returns live USD/TRY, gold, BIST100 index values in a single response. The `faz9/page.tsx` macro section shows news events (text), not live tick data.

---

## API Data Available Per Page

### UIUX-01: Dashboard / Briefing Card

**Existing endpoint (Phase 4):** `GET /api/briefing/today`

Response shape (confirmed from `briefing.py`):
```json
{
  "date": "2026-04-18",
  "kap_summary": "string | null",
  "price_summary": "string | null",
  "macro_summary": "string | null",
  "notable_stocks": [...],   // JSON — structure not further documented
  "ai_commentary": {...},    // JSON — structure not further documented
  "created_at": "ISO datetime",
  "generation_duration_ms": 1234
}
```

Returns **HTTP 404** with body `{"detail": "Brifing henüz üretilmedi"}` when cron has not run.

**Action:** Add `getBriefing()` to `lib/api.ts` + `BriefingData` type. Dashboard should call it with `catch` — 404 renders empty state, 200 renders card.

Supporting data still needed on dashboard:
- `getDashboard()` — for summary stats (can be kept as secondary section)
- `getStocks({ sort_by: 'overall_score', limit: 5 })` — top 5 AL signals as compact list below briefing

### UIUX-02: Stock Detail

All required data is available from two endpoints:

| Data | Endpoint | Field |
|------|----------|-------|
| OHLCV prices | `GET /api/stocks/{symbol}/prices?period=3m` | `prices[].{open,high,low,close,volume,date}` |
| SMA overlays | same | `prices[].{sma_20, sma_50, sma_200}` |
| Temel (fundamental) score | `GET /api/stocks/{symbol}` | `stock.fundamental_score` |
| Teknik (technical) score | same | `stock.technical_score` |
| Algı (sentiment) score | same | `stock.sentiment_score` |
| Overall score + recommendation | same | `stock.overall_score`, `stock.recommendation` |
| Technical signals text | `GET /api/stocks/{symbol}/technical` | `signals[].{name, direction, strength}` |
| AI justification text | **MISSING** — see gap note below | n/a |

**Gap — AI justification text (UIUX-02):** No per-stock AI commentary endpoint exists. Options:
1. Render the top 3 technical signals as a structured text block ("AI yorumu" placeholder using signal names)
2. Add a new backend endpoint `GET /api/stocks/{symbol}/commentary` in Phase 5 (adds scope)
3. Use `DailyBriefing.ai_commentary` if it contains per-stock commentary — structure unknown, needs investigation at implementation time

**Recommendation:** Option 1 for Phase 5 — render signals as structured summary. Annotate as "Teknik Özet" not "AI Yorumu" to be accurate.

### UIUX-03: Score Table

All required data is returned by `GET /api/stocks?sort_by=overall_score&limit=100`. The `StockSummary` type already includes `overall_score`, `technical_score`, `fundamental_score`, `sentiment_score`, `recommendation`.

Score-range filtering: the backend `GET /api/stocks` has no `min_score` / `max_score` query params. Add frontend-only filtering on the loaded array — no backend change needed since we load all 100 stocks at once.

### UIUX-04: Macro Panel

**Current state:** NO dedicated endpoint. The `GET /api/macro/events` returns news/text items joined to stocks via `NewsItem`, not live price data.

**Data needed:**
| Indicator | yfinance symbol | Already in backend? |
|-----------|----------------|---------------------|
| USD/TRY | `TRY=X` | In `MacroNewsCollector.macro_symbols` — fetched for news, not exposed as GET |
| Gold (USD) | `GC=F` | In `MacroNewsCollector.macro_symbols` |
| BIST 100 Index | `XU100.IS` | In `MacroNewsCollector.priority_bist` |
| Interest rate (faiz) | No yfinance symbol; TCMB published rate | Not in existing services |
| Inflation (TUIK) | No real-time feed; TUIK monthly release | Not in existing services |

**Recommendation:** Add `GET /api/macro/indicators` endpoint to `backend/app/api/macro.py` that:
1. Fetches `TRY=X`, `GC=F`, `XU100.IS` via yfinance (already a dependency)
2. Returns last-known TCMB policy rate and TUIK CPI from the `NewsItem` table (stored from past scans) as static cached values
3. Target latency: <2s with yfinance; add 60-second in-process cache

This is a small backend addition (~40 lines) that unlocks UIUX-04.

---

## Charting Library Decision

**Decision: Use `lightweight-charts` v5.1.0 — already installed, use `CandlestickSeries`.**

Confidence: HIGH — verified from `package.json` and `node_modules`.

### lightweight-charts v5 API (verified from `typings.d.ts`)

**Breaking change from v4:** In v5, series are added via `chart.addSeries(SeriesDefinition, options?)` — NOT `chart.addCandlestickSeries()`. The old `addCandlestickSeries()` is removed.

```typescript
// Source: /frontend/node_modules/lightweight-charts/dist/typings.d.ts
import { createChart, CandlestickSeries } from 'lightweight-charts';

const chart = createChart(containerRef.current, {
  layout: {
    background: { type: ColorType.Solid, color: '#0a0e1a' },
    textColor: '#94a3b8',
  },
  grid: {
    vertLines: { color: 'rgba(148,163,184,0.06)' },
    horzLines: { color: 'rgba(148,163,184,0.06)' },
  },
  width: containerRef.current.clientWidth,
  height: 360,
});

const series = chart.addSeries(CandlestickSeries, {
  upColor: '#22c55e',
  downColor: '#ef4444',
  borderVisible: false,
  wickUpColor: '#22c55e',
  wickDownColor: '#ef4444',
});

series.setData(prices.prices.map(p => ({
  time: p.date,          // 'YYYY-MM-DD' string — matches API output
  open: p.open,
  high: p.high,
  low: p.low,
  close: p.close,
})));
```

**SSR safety:** `createChart` requires a DOM element — must run inside `useEffect` with a `useRef<HTMLDivElement>`. The page is already `'use client'`. Always call `chart.remove()` in the cleanup function of `useEffect`.

**Resize handling:** Call `chart.applyOptions({ width: container.clientWidth })` inside a `ResizeObserver` callback and clean it up on unmount.

**Why not recharts?** Not installed. Installing adds 200KB+ gzip. lightweight-charts is purpose-built for financial OHLCV charts with superior performance.

**Why not the canvas hand-roll?** The existing canvas implementation (in stock detail) only draws close prices (line chart). CandlestickSeries requires no custom hit-testing, handles axes, crosshair, zoom, and time scale automatically.

---

## Architecture Patterns

### Recommended Component Structure for Phase 5

```
frontend/src/
├── components/
│   ├── ScoreRing.tsx              (existing — no change)
│   ├── StockHelpers.tsx           (existing — no change)
│   ├── Sidebar.tsx                (existing — add briefing nav item)
│   ├── BriefingCard.tsx           (NEW — UIUX-01)
│   ├── CandlestickPanel.tsx       (NEW — UIUX-02, wraps lightweight-charts)
│   ├── ScoreLayerPanel.tsx        (NEW — UIUX-02, temel/teknik/algı 3-layer)
│   └── MacroIndicatorBar.tsx      (NEW — UIUX-04)
├── app/
│   ├── page.tsx                   (REWRITE — briefing-first dashboard)
│   ├── page.module.css            (MODIFY — briefing card styles)
│   ├── stocks/
│   │   ├── page.tsx               (MODIFY — add score range filter)
│   │   └── [symbol]/
│   │       └── page.tsx           (MODIFY — replace canvas chart, add score layer)
│   └── macro/
│       └── page.tsx               (NEW — UIUX-04 macro panel page)
└── lib/
    └── api.ts                     (MODIFY — add getBriefing(), getMacroIndicators())
```

### Pattern: CandlestickPanel Component

```typescript
// Source: lightweight-charts v5.1.0 typings.d.ts
'use client';
import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, ColorType } from 'lightweight-charts';
import type { PricePoint } from '@/lib/api';

export default function CandlestickPanel({ prices }: { prices: PricePoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !prices.length) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      width: container.clientWidth,
      height: 360,
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    series.setData(prices.map(p => ({
      time: p.date as string,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    })));

    chart.timeScale().fitContent();

    const observer = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [prices]);

  return <div ref={containerRef} style={{ width: '100%' }} />;
}
```

### Pattern: BriefingCard with Empty State (UIUX-01)

```typescript
// 404 from GET /api/briefing/today → show empty state
// 200 → show briefing sections
async function loadBriefing() {
  try {
    const briefing = await api.getBriefing();
    setBriefing(briefing);
  } catch (err: any) {
    if (err.message?.includes('404') || err.message?.includes('Brifing')) {
      setBriefingState('not_generated');
    }
  }
}
```

### Pattern: Score Range Filter (UIUX-03)

Frontend-only filtering on loaded stocks array. No backend change needed.

```typescript
const filtered = stocks.filter(s => {
  if (minScore && (s.overall_score ?? 0) < minScore) return false;
  if (maxScore && (s.overall_score ?? 0) > maxScore) return false;
  if (filterRec && s.recommendation !== filterRec) return false;
  return true;
});
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candlestick chart | Canvas 2D OHLCV renderer | `lightweight-charts` v5 `CandlestickSeries` | Handles axes, crosshair, zoom, time scale, resize, performance |
| Live indicator refresh | setInterval polling | `useEffect` with cleanup on 60s + manual refresh button | Simpler, avoids memory leaks |
| CSS framework | Tailwind setup | Existing `globals.css` CSS variables | Design system already defined and consistent |
| Score color logic | Custom color function | Extend existing `ScoreRing.tsx` `getColor()` — already 5-tier | Already implemented and in use everywhere |

**Key insight:** The design system (CSS variables, `.card`, `.badge`, `.btn`) is complete. Every new component should compose these tokens — adding per-component CSS Modules only for layout-specific rules.

---

## Common Pitfalls

### Pitfall 1: lightweight-charts v5 Breaking API

**What goes wrong:** Using `chart.addCandlestickSeries()` (v4 API) in v5 throws `TypeError: chart.addCandlestickSeries is not a function`.

**Why it happens:** v5 removed all `add*Series()` shorthand methods. The new API is `chart.addSeries(CandlestickSeries, options)`.

**How to avoid:** Import `CandlestickSeries` (the series definition object) from `lightweight-charts` and pass it as the first argument to `addSeries`.

**Warning signs:** TypeScript will flag `addCandlestickSeries` as not existing on `IChartApi`. If TypeScript errors are suppressed (e.g., `any` cast), the error surfaces at runtime.

### Pitfall 2: createChart Called Before DOM Is Ready

**What goes wrong:** `createChart(containerRef.current, ...)` called when `containerRef.current` is `null` — throws `TypeError`.

**Why it happens:** `useEffect` with missing dependencies or called during SSR.

**How to avoid:** Guard with `if (!container || !prices.length) return;` inside `useEffect`. Pages are already `'use client'` — SSR is not the issue, but timing is.

### Pitfall 3: Chart Not Cleaned Up on Unmount

**What goes wrong:** Navigating away and back creates multiple chart instances on the same DOM node, causing visual artifacts and memory leaks.

**Why it happens:** `createChart` is called again before the previous chart is removed.

**How to avoid:** Always return a cleanup function from `useEffect`: `return () => { observer.disconnect(); chart.remove(); }`.

### Pitfall 4: useEffectEvent Misuse (Next.js 16 / React 19)

**What goes wrong:** The existing stock detail page uses `useEffectEvent` (React experimental hook). This is a React 19 feature — not stable in React 18. It appears to work in this codebase (React 19.2.4 is in `package.json`), but new code should prefer `useCallback` or plain functions inside `useEffect`.

**How to avoid:** When writing new components, use standard `useCallback` for event handlers. Do not introduce more `useEffectEvent` calls unless you have confirmed the pattern works end-to-end in this Next.js 16 + React 19 combination.

### Pitfall 5: Briefing 404 Treated as Error

**What goes wrong:** `api.getBriefing()` throws because the backend returns 404. The default error handler in `apiFetch` throws `Error(error.detail)` for any non-OK response. The dashboard shows an error state instead of the "not yet generated" empty state.

**Why it happens:** `apiFetch` does not distinguish 404 from 500.

**How to avoid:** In the dashboard's `loadBriefing()`, wrap in a try/catch and check `err.message` for the Turkish phrase `"Brifing henüz üretilmedi"` (set by the backend). Or, modify `apiFetch` to expose the HTTP status code in the thrown error.

### Pitfall 6: Macro Panel Has No Backend Data

**What goes wrong:** UIUX-04 implementation starts on the frontend before the backend endpoint exists, resulting in hardcoded placeholder values.

**Why it happens:** The research gap (no `GET /api/macro/indicators`) is not caught until implementation.

**How to avoid:** The first task in UIUX-04 implementation MUST be the backend endpoint. Frontend task is blocked on it. Sequence: backend endpoint → `lib/api.ts` update → MacroIndicatorBar component → MacroPage.

---

## Code Examples

### Adding getBriefing to lib/api.ts

```typescript
// Source: briefing.py response shape, confirmed
export interface BriefingData {
  date: string;
  kap_summary: string | null;
  price_summary: string | null;
  macro_summary: string | null;
  notable_stocks: unknown[] | null;   // JSON — structure TBD at impl time
  ai_commentary: unknown | null;       // JSON — structure TBD at impl time
  created_at: string | null;
  generation_duration_ms: number | null;
}

// In the api object:
getBriefing: () => apiFetch<BriefingData>('/briefing/today'),
```

### New Backend Macro Indicators Endpoint

```python
# Add to backend/app/api/macro.py
@router.get("/macro/indicators")
async def get_macro_indicators():
    """Live macro indicators: USD/TRY, gold, BIST100. Cached 60s."""
    import yfinance as yf
    tickers = yf.download(
        ["TRY=X", "GC=F", "XU100.IS"],
        period="2d", interval="1d", progress=False, auto_adjust=True
    )
    # parse last close for each, return dict
    # interest_rate and inflation returned as last known static values
```

### ScoreLayerPanel (3-layer: temel/teknik/algı)

```typescript
// UIUX-02: shows three score rings in a horizontal row with labels
// temel = fundamental_score, teknik = technical_score, algı = sentiment_score
function ScoreLayerPanel({ stock }: { stock: StockSummary }) {
  return (
    <div className="card" style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
      <ScoreRing score={stock.overall_score} size={80} strokeWidth={7} label="Genel" showLabel />
      <div style={{ width: 1, height: 60, background: 'var(--border-primary)' }} />
      <ScoreRing score={stock.fundamental_score} size={56} strokeWidth={5} label="Temel" showLabel />
      <ScoreRing score={stock.technical_score} size={56} strokeWidth={5} label="Teknik" showLabel />
      <ScoreRing score={stock.sentiment_score} size={56} strokeWidth={5} label="Algı" showLabel />
      <div style={{ marginLeft: 'auto' }}>
        <RecommendationBadge recommendation={stock.recommendation} />
      </div>
    </div>
  );
}
```

---

## Implementation Approach Per Requirement

### UIUX-01: Dashboard Briefing Card

**Files to modify:** `app/page.tsx`, `app/page.module.css`, `lib/api.ts`
**New files:** `components/BriefingCard.tsx`

1. Add `getBriefing()` and `BriefingData` to `lib/api.ts`
2. Create `BriefingCard.tsx` with two states: loaded (shows kap_summary, price_summary, macro_summary, notable_stocks) and empty (`briefingState === 'not_generated'` → "Sabah brifing henüz üretilmedi" message)
3. Rewrite `page.tsx` layout: BriefingCard at top (full width, prominent), stat cards in a compact row below, top-5 AL signals as a small list, remove the intelligence feed (it lives on `/intelligence`)
4. BriefingCard styling: `--bg-card` background, cyan left border accent, sections as labeled text blocks

### UIUX-02: Stock Detail Candlestick + Score Layer

**Files to modify:** `app/stocks/[symbol]/page.tsx`, `app/stocks/[symbol]/stock.module.css`
**New files:** `components/CandlestickPanel.tsx`, `components/ScoreLayerPanel.tsx`

1. Replace the `renderChart` canvas function with `CandlestickPanel` component
2. Remove the six-card `scoresGrid` above the tabs — replace with `ScoreLayerPanel` (one row: overall + temel/teknik/algı)
3. The "chart" tab becomes: CandlestickPanel + period selector buttons + SMA line overlays (via LineSeries added to same chart)
4. Below chart: "Teknik Özet" section showing top 3 signals as structured text (serves as AI justification placeholder)
5. Keep technical tab for detailed indicator table; keep causal tab

### UIUX-03: Score Table with Range Filter

**Files to modify:** `app/stocks/page.tsx`

1. Add two numeric inputs (or a dual-range slider): "Min Skor" and "Max Skor" (0-100)
2. Add `minScore` / `maxScore` state variables
3. Apply `filtered = stocks.filter(...)` before rendering — no backend change
4. Add score columns for temel/teknik/algı (currently only teknik + nedensellik shown; add temel + algı)
5. Make table header columns sortable client-side (fundamental_score, sentiment_score)

### UIUX-04: Macro Panel

**Files to create:** `backend/app/api/macro.py` (add endpoint), `app/macro/page.tsx`, `components/MacroIndicatorBar.tsx`, add `getMacroIndicators()` to `lib/api.ts`
**Sidebar:** Add `/macro` nav item to `Sidebar.tsx`

1. Backend: add `GET /api/macro/indicators` — yfinance fetch of TRY=X, GC=F, XU100.IS; static TCMB rate from NewsItem table or hardcoded latest
2. `lib/api.ts`: add `MacroIndicator` type and `getMacroIndicators()` call
3. `MacroIndicatorBar.tsx`: horizontal 5-tile layout, each tile shows label + value + daily change %; no navigation links within the panel
4. `app/macro/page.tsx`: full page with `Sidebar` + `MacroIndicatorBar` as hero + secondary section showing recent macro news from `getMacroEvents()`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `chart.addCandlestickSeries()` | `chart.addSeries(CandlestickSeries)` | lightweight-charts v5.0 | Breaking — must use new API |
| `chart.addLineSeries()` | `chart.addSeries(LineSeries)` | lightweight-charts v5.0 | Same breaking change |
| React 18 `useEffect` patterns | React 19 `useEffectEvent` (experimental) | React 19 RC | Exists in codebase; prefer `useCallback` for new code |
| Next.js params as object | Next.js 15+ params as `Promise<{...}>` unwrapped with `use()` | Next.js 15 | Already used correctly in `[symbol]/page.tsx` |

**Deprecated/outdated in this codebase:**
- Canvas line chart in `[symbol]/page.tsx`: works but is a hand-rolled approximation; replace with CandlestickSeries for UIUX-02

---

## Open Questions

1. **`notable_stocks` and `ai_commentary` shape in BriefingData**
   - What we know: Both are `JSON` columns in `DailyBriefing`; the API returns them as-is
   - What's unclear: The exact structure (array of `{symbol, text}` objects? nested dict?)
   - Recommendation: Add a `console.log` call in the BriefingCard during Wave 0 development to capture the live shape before building the render logic

2. **TCMB interest rate for UIUX-04**
   - What we know: TCMB policy rate is 42.5% as of April 2026 (from public knowledge); no automated fetch in codebase
   - What's unclear: Whether to auto-fetch from TCMB API or hardcode as a rarely-changing value with a manual update field
   - Recommendation: Store as a config constant in `backend/app/core/config.py` with a comment to update manually; not worth automated fetch for Phase 5

3. **TUIK inflation for UIUX-04**
   - What we know: TUIK publishes monthly; no feed in codebase
   - What's unclear: Same as above
   - Recommendation: Same approach — config constant

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected in frontend (no jest.config, no vitest.config, no pytest for frontend) |
| Config file | none — see Wave 0 gaps |
| Quick run command | `cd frontend && npm run build` (TypeScript compile gate) |
| Full suite command | `cd frontend && npm run lint && npm run build` |

The project has no test files for the frontend. Given `nyquist_validation: true`, validation relies on TypeScript compilation + lint as the automated gate. Runtime smoke testing is manual.

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UIUX-01 | Dashboard renders BriefingCard with correct sections | manual smoke | `npm run build` (TS compile) | ❌ Wave 0 |
| UIUX-01 | Empty state shown when briefing 404 | manual smoke | `npm run build` | ❌ Wave 0 |
| UIUX-02 | CandlestickPanel mounts without error | manual smoke | `npm run build` | ❌ Wave 0 |
| UIUX-02 | ScoreLayerPanel renders temel/teknik/algı rings | manual smoke | `npm run build` | ❌ Wave 0 |
| UIUX-03 | Score table filters by score range correctly | manual smoke | `npm run build` | ❌ Wave 0 |
| UIUX-04 | Macro panel loads indicators from new endpoint | manual smoke | `npm run build` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build`
- **Per wave merge:** `npm run lint && npm run build`
- **Phase gate:** Build green + manual browser smoke before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] No frontend test framework configured — TypeScript + lint serve as compile-time gate
- [ ] Manual smoke testing required for all four requirements
- [ ] Backend endpoint `GET /api/macro/indicators` must exist before any frontend work for UIUX-04

---

## Sources

### Primary (HIGH confidence)

- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/node_modules/lightweight-charts/dist/typings.d.ts` — v5.1.0 `addSeries`, `CandlestickSeries`, `createChart` signatures
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/package.json` — dependency versions verified
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/api/briefing.py` — exact response shape and 404 behavior
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/api/stocks.py` — all stock endpoints confirmed
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/backend/app/api/macro.py` — confirmed no indicators endpoint
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/app/page.tsx` — current dashboard structure
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/app/stocks/[symbol]/page.tsx` — current chart implementation
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/lib/api.ts` — all wired API functions
- `/Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/app/globals.css` — design system tokens

### Secondary (MEDIUM confidence)

- `node_modules/lightweight-charts/dist/lightweight-charts.standalone.development.js` — confirmed `createChart` and `CandlestickSeries` are exported in runtime bundle

### Tertiary (LOW confidence)

- TCMB policy rate 42.5% (April 2026) — public knowledge, not verified against TCMB API at research time

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified from installed node_modules
- Architecture: HIGH — based on direct source reading of existing pages
- API data shapes: HIGH — verified from backend Python source
- Pitfalls: HIGH — v5 breaking changes verified from typings.d.ts
- Macro endpoint gap: HIGH — confirmed absence by reading macro.py in full

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (stable dependencies; lightweight-charts API unlikely to change)
