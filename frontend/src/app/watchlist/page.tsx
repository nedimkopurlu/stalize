'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
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

// ─── Page ────────────────────────────────────────────────────

export default function WatchlistPage() {
  const router = useRouter();
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');
  const [watchSymbols, setWatchSymbols] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const stored = JSON.parse(localStorage.getItem('stalize-watchlist') || '[]') as string[];
        const symbols = Array.from(new Set(stored.filter(Boolean)));
        if (!cancelled) setWatchSymbols(symbols);
        if (symbols.length === 0) {
          if (!cancelled) setStocks([]);
          return;
        }
        const res = await api.getStocks({ symbols: symbols.join(','), limit: symbols.length });
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
              {loading ? '— hisse takipte' : `${displayed.length}/${watchSymbols.length} hisse takipte`}
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
                    <th className={styles.hideMobile}>Şirket</th>
                    <th className={styles.hideMobile}>Sektör</th>
                    <th className={styles.right}>Fiyat</th>
                    <th className={styles.right}>Değişim</th>
                    <th className={styles.right}>Skor</th>
                    <th className={`${styles.right} ${styles.hideMobile}`}>Hacim</th>
                    <th className={styles.right}>☆</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    Array.from({ length: 10 }).map((_, i) => (
                      <tr key={i} className={styles.skeletonRow}>
                        {Array.from({ length: 8 }).map((__, j) => (
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
                      <td colSpan={8}>
                        <div className={styles.empty}>
                          {watchSymbols.length === 0 ? (
                            <>
                              <div className={styles.emptyIcon}>⭐</div>
                              <div className={styles.emptyTitle}>Takip listeniz boş</div>
                              <p className={styles.emptyDesc}>Bir hisse detay sayfasında yıldız ikonuna tıklayarak ekleyebilirsiniz.</p>
                              <a href="/stocks" className={styles.emptyAction}>Hisselere Göz At →</a>
                            </>
                          ) : (
                            <>
                              <div className={styles.emptyIcon}>🔍</div>
                              <div className={styles.emptyTitle}>Sonuç bulunamadı</div>
                              <p className={styles.emptyDesc}>Bu filtreyle eşleşen hisse bulunamadı.</p>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ) : (
                    displayed.map((s, index) => {
                      const change = s.daily_change_pct;
                      const isUp = (change ?? 0) >= 0;
                      return (
                        <tr
                          key={`${s.symbol}-${index}`}
                          onClick={() => router.push(`/stocks/${s.symbol}`)}
                        >
                          <td>
                            <div className={styles.symbol}>{s.symbol}</div>
                          </td>
                          <td className={styles.hideMobile}>
                            <div className={styles.companyName} title={s.name ?? undefined}>
                              {s.name ?? '—'}
                            </div>
                          </td>
                          <td className={styles.hideMobile}>
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
                          <td className={styles.hideMobile}>
                            <div className={styles.volume}>{formatVolume(s.volume)}</div>
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
