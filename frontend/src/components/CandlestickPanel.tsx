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

    // v5 API: use chart.addSeries(CandlestickSeries, ...) — NOT addCandlestickSeries
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

  if (prices.length === 0) {
    return (
      <div style={{ minHeight: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        Fiyat verisi yükleniyor...
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', minHeight: 360 }}
    />
  );
}
