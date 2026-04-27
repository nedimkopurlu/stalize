'use client';

import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, LineSeries, HistogramSeries, ColorType } from 'lightweight-charts';
import type { PricePoint } from '@/lib/api';

interface EMAPoint {
  date: string;
  value: number;
}

interface CandlestickEMAPanelProps {
  prices: PricePoint[];
  ema50?: EMAPoint[];
  ema200?: EMAPoint[];
}

export default function CandlestickEMAPanel({ prices, ema50 = [], ema200 = [] }: CandlestickEMAPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || prices.length === 0) return;

    // Volume average — highlight bars above average
    const volumes = prices.map(p => p.volume ?? 0);
    const avgVol = volumes.reduce((a, b) => a + b, 0) / (volumes.length || 1);

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(148,163,184,0.06)' },
        horzLines: { color: 'rgba(148,163,184,0.06)' },
      },
      crosshair: {
        vertLine: { color: 'rgba(148,163,184,0.3)' },
        horzLine: { color: 'rgba(148,163,184,0.3)' },
      },
      width: container.clientWidth,
      height: 480,
      timeScale: {
        borderColor: 'rgba(148,163,184,0.1)',
        timeVisible: false,
      },
    });

    // ── Candlestick series ──
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });
    candleSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.05, bottom: 0.40 },
    });

    const candleData = prices
      .filter(p => p.open != null && p.high != null && p.low != null && p.close != null)
      .map(p => ({ time: p.date as string, open: p.open, high: p.high, low: p.low, close: p.close }));
    candleSeries.setData(candleData);

    // ── EMA 50 — orange ──
    if (ema50.length > 0) {
      const ema50Series = chart.addSeries(LineSeries, {
        color: '#f97316',
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      ema50Series.priceScale().applyOptions({
        scaleMargins: { top: 0.05, bottom: 0.40 },
      });
      ema50Series.setData(ema50.map(e => ({ time: e.date as string, value: e.value })));
    }

    // ── EMA 200 — blue ──
    if (ema200.length > 0) {
      const ema200Series = chart.addSeries(LineSeries, {
        color: '#3b82f6',
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      ema200Series.priceScale().applyOptions({
        scaleMargins: { top: 0.05, bottom: 0.40 },
      });
      ema200Series.setData(ema200.map(e => ({ time: e.date as string, value: e.value })));
    }

    // ── Volume histogram ──
    const volSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'volume',
      priceLineVisible: false,
      lastValueVisible: false,
    });
    volSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.72, bottom: 0.14 },
    });
    const volData = prices
      .filter(p => p.volume != null)
      .map(p => ({
        time: p.date as string,
        value: p.volume ?? 0,
        color: (p.volume ?? 0) > avgVol ? 'rgba(59,130,246,0.8)' : 'rgba(59,130,246,0.35)',
      }));
    volSeries.setData(volData);

    // ── RSI line ──
    const rsiPoints = prices.filter(p => p.rsi_14 != null);
    if (rsiPoints.length > 0) {
      const rsiSeries = chart.addSeries(LineSeries, {
        color: '#a855f7',
        lineWidth: 2,
        priceScaleId: 'rsi',
        priceLineVisible: false,
        lastValueVisible: false,
      });
      rsiSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.84, bottom: 0.0 },
      });
      rsiSeries.setData(rsiPoints.map(p => ({ time: p.date as string, value: p.rsi_14! })));
      // RSI reference lines at 70 and 30
      rsiSeries.createPriceLine({ price: 70, color: 'rgba(239,68,68,0.45)', lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: '' });
      rsiSeries.createPriceLine({ price: 30, color: 'rgba(34,197,94,0.45)', lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: '' });
    }

    chart.timeScale().fitContent();

    const observer = new ResizeObserver(() => {
      if (container) chart.applyOptions({ width: container.clientWidth });
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [prices, ema50, ema200]);

  if (prices.length === 0) {
    return (
      <div style={{ minHeight: 480, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        Fiyat verisi yükleniyor...
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', minHeight: 480 }} />;
}
