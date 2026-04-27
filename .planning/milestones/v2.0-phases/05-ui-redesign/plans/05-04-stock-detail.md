---
phase: 05-ui-redesign
plan_id: 05-04
title: "Stock Detail — Candlestick Chart + 3-Layer Scores (UIUX-02)"
requirements: [UIUX-02]
wave: 4
estimated_minutes: 55
autonomous: true
depends_on: [05-01]
files_modified:
  - frontend/src/components/CandlestickPanel.tsx
  - frontend/src/components/ScoreLayerPanel.tsx
  - frontend/src/app/stocks/[symbol]/page.tsx
must_haves:
  truths:
    - "Stock detail page shows a candlestick chart (green/red candles) instead of the existing line chart"
    - "Three score rings labelled Temel, Teknik, Algı are visible in a single row below the overall score"
    - "Teknik Ozet section shows the top 3 technical signals as structured text"
    - "No JavaScript errors on chart mount or unmount when navigating away and back"
  artifacts:
    - path: "frontend/src/components/CandlestickPanel.tsx"
      provides: "lightweight-charts v5 candlestick component with resize handling and cleanup"
    - path: "frontend/src/components/ScoreLayerPanel.tsx"
      provides: "3-layer score display: overall + temel/teknik/algi rings"
    - path: "frontend/src/app/stocks/[symbol]/page.tsx"
      provides: "Modified stock detail using CandlestickPanel + ScoreLayerPanel"
  key_links:
    - from: "frontend/src/app/stocks/[symbol]/page.tsx"
      to: "frontend/src/components/CandlestickPanel.tsx"
      via: "import CandlestickPanel; render with prices={stockPrices.prices}"
    - from: "frontend/src/components/CandlestickPanel.tsx"
      to: "lightweight-charts CandlestickSeries"
      via: "chart.addSeries(CandlestickSeries, options) — NOT addCandlestickSeries"
---

<objective>
Replace the hand-rolled canvas line chart on the stock detail page with a proper `lightweight-charts` v5 candlestick chart, and replace the six-card score grid with a unified ScoreLayerPanel showing overall + temel/teknik/algi rings in a single row. Add a "Teknik Ozet" section showing top 3 technical signals.

Purpose: Implements UIUX-02 — candlestick price chart + 3-layer scores + Teknik Ozet in single view.
Output: CandlestickPanel.tsx, ScoreLayerPanel.tsx, modified [symbol]/page.tsx
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/05-ui-redesign/05-CONTEXT.md
@.planning/phases/05-ui-redesign/RESEARCH.md
@.planning/phases/05-ui-redesign/VALIDATION.md

<interfaces>
<!-- lightweight-charts v5 API — verified from node_modules/lightweight-charts/dist/typings.d.ts -->
```typescript
import { createChart, CandlestickSeries, ColorType } from 'lightweight-charts';
// createChart(container: HTMLElement, options): IChartApi
// chart.addSeries(CandlestickSeries, options): ISeriesApi<'Candlestick'>
// series.setData(data: CandlestickData[]): void
// chart.timeScale().fitContent(): void
// chart.applyOptions({ width: number }): void
// chart.remove(): void   ← MUST call in useEffect cleanup
// CandlestickData: { time: string, open: number, high: number, low: number, close: number }
```

<!-- PricePoint from api.ts -->
```typescript
export interface PricePoint {
  date: string;   // 'YYYY-MM-DD' — maps directly to lightweight-charts 'time'
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma_20?: number | null;
  sma_50?: number | null;
  sma_200?: number | null;
}
```

<!-- StockSummary scores -->
```typescript
export interface StockSummary {
  technical_score: number | null;
  fundamental_score: number | null;
  sentiment_score: number | null;
  overall_score: number | null;
  recommendation: string | null;
}
// temel = fundamental_score, teknik = technical_score, algi = sentiment_score
```

<!-- TechnicalResult from api.ts -->
```typescript
export interface TechnicalResult {
  signals: Array<{ type: string; name: string; direction: string; strength: number }>;
}
```

<!-- ScoreRing existing props -->
```typescript
// frontend/src/components/ScoreRing.tsx — existing component
// Props: score (number | null), size (number), strokeWidth (number), showLabel? (boolean), label? (string)
```

<!-- RecommendationBadge existing props -->
```typescript
// frontend/src/components/StockHelpers.tsx
// export default function RecommendationBadge({ recommendation }: { recommendation: string | null })
```

<!-- Warning from AGENTS.md -->
// This project uses Next.js with breaking changes. Read node_modules/next/dist/docs/ before writing code.
// The stock detail page uses Next.js 15+ async params: `const { symbol } = use(params)` pattern.
// Do NOT use the old `params.symbol` without unwrapping — it is a Promise in Next.js 15+.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create CandlestickPanel.tsx and ScoreLayerPanel.tsx</name>
  <files>
    frontend/src/components/CandlestickPanel.tsx
    frontend/src/components/ScoreLayerPanel.tsx
  </files>
  <action>
Create `frontend/src/components/CandlestickPanel.tsx`:

```typescript
'use client';

import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, ColorType } from 'lightweight-charts';
import type { PricePoint } from '@/lib/api';

interface CandlestickPanelProps {
  prices: PricePoint[];
}

export default function CandlestickPanel({ prices }: CandlestickPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || prices.length === 0) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(148, 163, 184, 0.06)' },
        horzLines: { color: 'rgba(148, 163, 184, 0.06)' },
      },
      crosshair: {
        vertLine: { color: 'rgba(148, 163, 184, 0.3)' },
        horzLine: { color: 'rgba(148, 163, 184, 0.3)' },
      },
      width: container.clientWidth,
      height: 360,
      timeScale: {
        borderColor: 'rgba(148, 163, 184, 0.1)',
        timeVisible: false,
      },
      rightPriceScale: {
        borderColor: 'rgba(148, 163, 184, 0.1)',
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const candleData = prices
      .filter((p) => p.open != null && p.high != null && p.low != null && p.close != null)
      .map((p) => ({
        time: p.date as string,
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
      }));

    candleSeries.setData(candleData);
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(() => {
      if (container) {
        chart.applyOptions({ width: container.clientWidth });
      }
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [prices]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', minHeight: 360 }}
    />
  );
}
```

Create `frontend/src/components/ScoreLayerPanel.tsx`:

```typescript
'use client';

import React from 'react';
import ScoreRing from '@/components/ScoreRing';
import RecommendationBadge from '@/components/StockHelpers';
import type { StockSummary } from '@/lib/api';

interface ScoreLayerPanelProps {
  stock: StockSummary;
}

export default function ScoreLayerPanel({ stock }: ScoreLayerPanelProps) {
  return (
    <div
      className="card"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        flexWrap: 'wrap',
        marginBottom: 16,
        padding: '16px 20px',
      }}
    >
      {/* Overall score — larger ring */}
      <ScoreRing score={stock.overall_score} size={72} strokeWidth={6} showLabel label="Genel" />

      {/* Vertical divider */}
      <div style={{ width: 1, height: 52, background: 'var(--border-primary, rgba(148,163,184,0.1))', flexShrink: 0 }} />

      {/* 3-layer scores */}
      <ScoreRing score={stock.fundamental_score} size={52} strokeWidth={4} showLabel label="Temel" />
      <ScoreRing score={stock.technical_score} size={52} strokeWidth={4} showLabel label="Teknik" />
      <ScoreRing score={stock.sentiment_score} size={52} strokeWidth={4} showLabel label="Algi" />

      {/* Recommendation badge pushed right */}
      <div style={{ marginLeft: 'auto' }}>
        <RecommendationBadge recommendation={stock.recommendation} />
      </div>
    </div>
  );
}
```

Note: `ScoreRing` already has a `showLabel` prop that renders the label text below the ring — verified from existing codebase usage. If the `label` prop does not exist on ScoreRing, pass the label as a sibling `<span>` instead.
  </action>
  <verify>
    <automated>grep -n "export default function CandlestickPanel\|export default function ScoreLayerPanel" /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/components/CandlestickPanel.tsx /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend/src/components/ScoreLayerPanel.tsx</automated>
  </verify>
  <done>Both components exported. CandlestickPanel uses `chart.addSeries(CandlestickSeries, ...)` (NOT addCandlestickSeries). ScoreLayerPanel renders four ScoreRing components (Genel, Temel, Teknik, Algi).</done>
</task>

<task type="auto">
  <name>Task 2: Replace canvas chart and score grid in stock detail page</name>
  <files>frontend/src/app/stocks/[symbol]/page.tsx</files>
  <action>
Read the current `frontend/src/app/stocks/[symbol]/page.tsx` fully before editing. Then make the following changes:

**1. Add imports** at the top:
```typescript
import CandlestickPanel from '@/components/CandlestickPanel';
import ScoreLayerPanel from '@/components/ScoreLayerPanel';
```

**2. Remove the canvas chart function.** The existing page likely has a `renderChart` or similar function that uses `canvas.getContext('2d')` and draws price data manually. Remove the entire function and any `useRef` for the canvas element. Keep `useRef` for the chart container if it's used elsewhere, but the canvas-based drawing code must go.

**3. Replace the chart tab content.** Find where the chart tab renders (inside a conditional like `activeTab === 'chart'` or similar). Replace the `<canvas>` element and any surrounding chart-rendering wrapper with:

```tsx
{/* Candlestick chart (UIUX-02) */}
{stockPrices && stockPrices.prices.length > 0 ? (
  <CandlestickPanel prices={stockPrices.prices} />
) : (
  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
    Fiyat verisi yükleniyor...
  </div>
)}
```

The variable name for the price data may be `stockPrices`, `prices`, or similar — use whatever name the existing page uses for the result of `api.getStockPrices()`.

**4. Replace the scores grid.** Find the existing scores section — likely a `.scoresGrid` div containing multiple `ScoreRing` components for technical_score, fundamental_score, sentiment_score, overall_score, etc. Replace that entire block with:

```tsx
{/* 3-layer score panel (UIUX-02) */}
{stock && <ScoreLayerPanel stock={stock.stock} />}
```

Place this immediately above the tab bar / chart area.

**5. Add Teknik Ozet section** inside the chart tab, BELOW the CandlestickPanel:

```tsx
{/* Teknik Ozet — top 3 signals as structured text (UIUX-02) */}
{technical && technical.signals.length > 0 && (
  <div className="card" style={{ marginTop: 16 }}>
    <div style={{ fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12 }}>
      Teknik Ozet
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {technical.signals.slice(0, 3).map((signal, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: '0.72rem',
            fontWeight: 600,
            background: signal.direction === 'bullish' ? 'rgba(34,197,94,0.1)' : signal.direction === 'bearish' ? 'rgba(239,68,68,0.1)' : 'rgba(148,163,184,0.1)',
            color: signal.direction === 'bullish' ? '#22c55e' : signal.direction === 'bearish' ? '#ef4444' : '#94a3b8',
          }}>
            {signal.direction === 'bullish' ? 'AL' : signal.direction === 'bearish' ? 'SAT' : 'NOTR'}
          </span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{signal.name}</span>
          <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
            {(signal.strength * 100).toFixed(0)}%
          </span>
        </div>
      ))}
    </div>
  </div>
)}
```

The `technical` variable should already be fetched via `api.getStockTechnical(symbol)` in the existing page. If not, add a `useState<TechnicalResult | null>` and fetch it in `useEffect` alongside the other data.

**6. Do NOT remove** the existing technical tab (detailed signals table) or the causal tab. Only the chart tab gets the new CandlestickPanel, and the scores area (above the tabs) gets ScoreLayerPanel.

**7. TypeScript check** — if ScoreRing does not accept a `label` prop, adjust ScoreLayerPanel to render a `<div>` label manually below each ring instead.
  </action>
  <verify>
    <automated>cd /Users/nedimkopurlu/Downloads/PROJELER/stalize/frontend && npm run build 2>&1 | tail -30</automated>
  </verify>
  <done>
- `npm run build` exits 0 (no TS errors)
- `grep "CandlestickPanel\|ScoreLayerPanel" frontend/src/app/stocks/[symbol]/page.tsx` shows both used
- No `canvas.getContext` references remain in stock detail page
- `grep "addCandlestickSeries" frontend/src/components/CandlestickPanel.tsx` returns empty (v5 API used correctly)
  </done>
</task>

</tasks>

<verification>
1. `npm run build` — exits 0
2. `grep -c "addSeries" frontend/src/components/CandlestickPanel.tsx` — returns 1 (correct v5 call)
3. `grep "addCandlestickSeries" frontend/src/components/CandlestickPanel.tsx` — returns empty
4. `grep "canvas" frontend/src/app/stocks/\[symbol\]/page.tsx` — returns empty or only non-chart usages
5. Manual smoke: navigate to /stocks/THYAO — see green/red candlestick chart, three score rings (Temel/Teknik/Algi), and Teknik Ozet with up to 3 signals
6. Navigate away and back — no console errors from chart double-mount
</verification>

<success_criteria>
- Candlestick chart renders with green up-candles and red down-candles (UIUX-02)
- ScoreLayerPanel shows Genel (overall) + Temel (fundamental) + Teknik (technical) + Algi (sentiment) in one row
- Teknik Ozet shows up to 3 signals with direction badge + name + strength %
- Chart cleanup on unmount works (no ResizeObserver leaks, no duplicate chart instances)
- TypeScript build clean
</success_criteria>

<output>
After completion, create `.planning/phases/05-ui-redesign/plans/05-04-SUMMARY.md` documenting the lightweight-charts v5 API calls used, the component props, and any workarounds needed for the ScoreRing label prop.
</output>
