'use client';

import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, LineSeries } from 'lightweight-charts';
import { PortfolioComparisonPoint } from '@/lib/api';
import styles from './BistComparisonChart.module.css';

export default function BistComparisonChart({
  portfolioSeries,
  benchmarkSeries,
  benchmarkLabel = 'BIST100',
}: {
  portfolioSeries: PortfolioComparisonPoint[];
  benchmarkSeries: PortfolioComparisonPoint[];
  benchmarkLabel?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const portfolioPoints = portfolioSeries;
  const benchmarkPoints = benchmarkSeries;
  const hasData = portfolioPoints.some((point) => point.return_pct !== null) || benchmarkPoints.some((point) => point.return_pct !== null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(148,163,184,0.08)' },
        horzLines: { color: 'rgba(148,163,184,0.08)' },
      },
      rightPriceScale: { borderColor: 'rgba(148,163,184,0.1)' },
      timeScale: { borderColor: 'rgba(148,163,184,0.1)' },
    });

    // Veri gelmediğinde dürüst boş seri render edilir.
    const portfolioSeries = chart.addSeries(LineSeries, {
      color: '#22d3ee',
      lineWidth: 2,
      title: 'Portföy',
    });
    portfolioSeries.setData(
      portfolioPoints
        .filter((point) => point.return_pct !== null)
        .map((point) => ({ time: point.date, value: Number(point.return_pct) }))
    );

    // Veri gelmediğinde dürüst boş seri render edilir.
    const bistSeries = chart.addSeries(LineSeries, {
      color: '#a855f7',
      lineWidth: 2,
      title: benchmarkLabel,
    });
    bistSeries.setData(
      benchmarkPoints
        .filter((point) => point.return_pct !== null)
        .map((point) => ({ time: point.date, value: Number(point.return_pct) }))
    );

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [benchmarkLabel, benchmarkPoints, portfolioPoints]);

  return (
    <div className={`card ${styles.card}`}>
      <div className={styles.header}>
        <span className={styles.title}>Kümülatif Getiri</span>
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={`${styles.legendLine} ${styles.legendLinePortfolio}`} />
            Portföy
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.legendLine} ${styles.legendLineBenchmark}`} />
            {benchmarkLabel}
          </span>
        </div>
      </div>
      <div className={styles.subtext}>
        {hasData
          ? 'Portföy ve benchmark kümülatif getiri serileri son snapshot verileriyle hesaplandı.'
          : 'Karşılaştırma serisi henüz oluşmadı. Geçmiş snapshot verisi geldiğinde grafik dolacaktır.'}
      </div>
      <div ref={containerRef} className={styles.chart} />
    </div>
  );
}
