'use client';

import { useEffect, useRef } from 'react';
import { SparklinePoint } from '@/lib/api';

interface Props {
  points: SparklinePoint[];
  label: string;
  color?: string;
  height?: number;
}

export default function SparklineWidget({ points, label, color, height = 60 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Determine trend color if not provided
  const trendColor =
    color ??
    (points.length >= 2 && points[points.length - 1].close > points[0].close
      ? '#10b981'
      : '#ef4444');

  useEffect(() => {
    if (!containerRef.current || points.length === 0) return;

    let chart: import('lightweight-charts').IChartApi | null = null;

    (async () => {
      const { createChart, AreaSeries } = await import('lightweight-charts');

      if (!containerRef.current) return;

      chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height,
        layout: {
          background: { color: 'transparent' },
          textColor: 'rgba(255,255,255,0)',
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { visible: false },
        },
        crosshair: { horzLine: { visible: false }, vertLine: { visible: false } },
        rightPriceScale: { visible: false },
        leftPriceScale: { visible: false },
        timeScale: { visible: false, borderVisible: false },
        handleScroll: false,
        handleScale: false,
      });

      const series = chart.addSeries(AreaSeries, {
        lineColor: trendColor,
        topColor: `${trendColor}33`,
        bottomColor: `${trendColor}00`,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });

      const data = points.map((p) => ({
        time: p.date as import('lightweight-charts').Time,
        value: p.close,
      }));

      series.setData(data);
      chart.timeScale().fitContent();
    })();

    return () => {
      chart?.remove();
    };
  }, [points, trendColor, height]);

  if (points.length === 0) {
    return (
      <div
        className="glass-card"
        style={{ padding: 12 }}
      >
        <div
          style={{
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: 8,
          }}
        >
          {label}
        </div>
        <div
          style={{
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
          }}
        >
          Veri yok
        </div>
      </div>
    );
  }

  const lastPoint = points[points.length - 1];
  const firstPoint = points[0];
  const changePct =
    firstPoint.close !== 0
      ? ((lastPoint.close - firstPoint.close) / firstPoint.close) * 100
      : 0;

  return (
    <div className="glass-card" style={{ padding: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 6,
        }}
      >
        <span
          style={{
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: trendColor,
          }}
        >
          {changePct >= 0 ? '+' : ''}
          {changePct.toFixed(2)}%
        </span>
      </div>
      <div ref={containerRef} style={{ width: '100%', height }} />
    </div>
  );
}
