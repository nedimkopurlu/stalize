'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import Sparkline from '@/components/Sparkline';
import { formatPrice, formatVolume } from '@/components/StockHelpers';
import api, { StockSummary } from '@/lib/api';
import styles from './page.module.css';

// ─── Filter Types ────────────────────────────────────────────

type FilterKey = 'all' | 'up' | 'down' | 'volume';

const FILTER_LABELS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'Tümü' },
  { key: 'up', label: 'Yükselenler' },
  { key: 'down', label: 'Düşenler' },
  { key: 'volume', label: 'Hacim' },
];

// ─── Helpers ─────────────────────────────────────────────────

function applyFilter(stocks: StockSummary[], filter: FilterKey): StockSummary[] {
  switch (filter) {
    case 'up':
      return stocks.filter((s) => (s.daily_change_pct ?? 0) > 0);
    case 'down':
      return stocks.filter((s) => (s.daily_change_pct ?? 0) < 0);
    case 'volume':
      return [...stocks].sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0));
    default:
      return stocks;
  }
}

function sparklineSeed(symbol: string): number {
  return symbol.charCodeAt(0) * 7 + (symbol.charCodeAt(2) || 1);
}

function sparklineColor(change: number | null): string {
  return (change ?? 0) >= 0 ? '#10b981' : '#ef4444';
}

// ─── Page ────────────────────────────────────────────────────

export default function WatchlistPage() {
  const router = useRouter();
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getStocks({ limit: 100 });
        if (!cancelled) setStocks(res.stocks);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Veriler alınamadı');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadData();
    return () => { cancelled = true; };
  }, []);

  const displayed = applyFilter(stocks, filter);

  return (
    <AppShell>
      <div className={styles.page}>
        {/* ── Header ── */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <p className={styles.eyebrow}>Takip Listem</p>
            <h1 className={styles.title}>
              {loading ? '— hisse takipte' : `${displayed.length} hisse takipte`}
            </h1>
          </div>

          <div className={styles.filterGroup}>
            {FILTER_LABELS.map(({ key, label }) => (
              <button
                key={key}
                className={`${styles.pill} ${filter === key ? styles.pillActive : ''}`}
                onClick={() => setFilter(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Table Card ── */}
        <div className={styles.tableCard}>
          {error ? (
            <div className={styles.error}>{error}</div>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th>Şirket</th>
                    <th>Sektör</th>
                    <th className={styles.right}>Fiyat</th>
                    <th className={styles.right}>Değişim</th>
                    <th className={styles.right}>Skor</th>
                    <th className={styles.right}>Hacim</th>
                    <th className={styles.center}>Trend</th>
                    <th className={styles.right}>☆</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    Array.from({ length: 10 }).map((_, i) => (
                      <tr key={i} className={styles.skeletonRow}>
                        {Array.from({ length: 9 }).map((__, j) => (
                          <td key={j}>
                            <div
                              className={styles.skeletonLine}
                              style={{ width: j === 0 ? 48 : j === 1 ? 120 : j === 7 ? 70 : 64 }}
                            />
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : displayed.length === 0 ? (
                    <tr>
                      <td colSpan={9}>
                        <div className={styles.empty}>
                          Bu filtreyle eşleşen hisse bulunamadı.
                        </div>
                      </td>
                    </tr>
                  ) : (
                    displayed.map((s) => {
                      const change = s.daily_change_pct;
                      const isUp = (change ?? 0) >= 0;
                      return (
                        <tr
                          key={s.symbol}
                          onClick={() => router.push(`/stocks/${s.symbol}`)}
                        >
                          <td>
                            <div className={styles.symbol}>{s.symbol}</div>
                          </td>
                          <td>
                            <div className={styles.companyName} title={s.name ?? undefined}>
                              {s.name ?? '—'}
                            </div>
                          </td>
                          <td>
                            <span className={styles.sector}>{s.sector ?? '—'}</span>
                          </td>
                          <td>
                            <div className={styles.price}>{formatPrice(s.current_price)}</div>
                          </td>
                          <td>
                            <div
                              className={`${styles.change} ${isUp ? styles.changeUp : styles.changeDown}`}
                            >
                              {change === null || change === undefined
                                ? '—'
                                : `${isUp ? '+' : ''}${change.toFixed(2)}%`}
                            </div>
                          </td>
                          <td>
                            <div className={styles.score}>
                              {s.overall_score !== null && s.overall_score !== undefined
                                ? s.overall_score.toFixed(1)
                                : '—'}
                            </div>
                          </td>
                          <td>
                            <div className={styles.volume}>{formatVolume(s.volume)}</div>
                          </td>
                          <td className={styles.trendCell}>
                            <Sparkline
                              seed={sparklineSeed(s.symbol)}
                              color={sparklineColor(change)}
                              width={70}
                              height={22}
                            />
                          </td>
                          <td className={styles.starCell}>
                            <span className={styles.star}>★</span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
