'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import { formatPrice, formatVolume, formatMarketCap } from '@/components/StockHelpers';
import api, { StockSummary } from '@/lib/api';
import styles from './page.module.css';

// ── Types ──────────────────────────────────────────────────

type SortKey = 'symbol' | 'name' | 'sector' | 'current_price' | 'daily_change_pct' | 'fundamental_score' | 'market_cap' | 'volume';
type SortDir = 'asc' | 'desc';

// ── Helpers ────────────────────────────────────────────────

function SortIcon({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDir }) {
  if (col !== sortKey) {
    return <span className={styles.sortIconInactive}>↕</span>;
  }
  return <span className={styles.sortIconActive}>{sortDir === 'asc' ? '↑' : '↓'}</span>;
}

// ── Skeleton rows ──────────────────────────────────────────

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 12 }).map((_, i) => (
        <tr key={i} className={styles.skeletonRow}>
          {Array.from({ length: 8 }).map((__, j) => (
            <td key={j}>
              <div className={styles.skeletonCell} style={{ width: j === 1 ? 140 : j === 2 ? 100 : 60 }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// ── Page ──────────────────────────────────────────────────

export default function StocksPage() {
  const router = useRouter();

  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [sectors, setSectors] = useState<string[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('symbol');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  // Fetch sector list
  useEffect(() => {
    api.getStockSectors()
      .then((res) => setSectors(res.sectors))
      .catch(() => { /* non-critical */ });
  }, []);

  // Fetch stocks on mount
  useEffect(() => {
    setLoading(true);
    setLoadError(null);
    api.getStocks({ sort_by: 'overall_score', limit: 100 })
      .then((res) => {
        setStocks(res.stocks);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        setLoadError(err instanceof Error ? err.message : 'Hisse listesi alınamadı');
      })
      .finally(() => setLoading(false));
  }, []);

  // Client-side filter + sort
  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let list = stocks.filter((s) => {
      const matchSearch = !q || s.symbol.toLowerCase().includes(q) || (s.name ?? '').toLowerCase().includes(q);
      const matchSector = !sectorFilter || s.sector === sectorFilter;
      return matchSearch && matchSector;
    });

    list = [...list].sort((a, b) => {
      let av: string | number | null = null;
      let bv: string | number | null = null;

      switch (sortKey) {
        case 'symbol': av = a.symbol; bv = b.symbol; break;
        case 'name': av = a.name ?? ''; bv = b.name ?? ''; break;
        case 'sector': av = a.sector ?? ''; bv = b.sector ?? ''; break;
        case 'current_price': av = a.current_price; bv = b.current_price; break;
        case 'daily_change_pct': av = a.daily_change_pct; bv = b.daily_change_pct; break;
        case 'fundamental_score': av = a.fundamental_score; bv = b.fundamental_score; break;
        case 'market_cap': av = a.market_cap; bv = b.market_cap; break;
        case 'volume': av = a.volume; bv = b.volume; break;
      }

      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv, 'tr') : bv.localeCompare(av, 'tr');
      }
      const an = av as number;
      const bn = bv as number;
      return sortDir === 'asc' ? an - bn : bn - an;
    });

    return list;
  }, [stocks, search, sectorFilter, sortKey, sortDir]);

  function toggleSort(col: SortKey) {
    if (col === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col);
      setSortDir('asc');
    }
  }

  function handleRowClick(symbol: string) {
    router.push('/stocks/' + symbol);
  }

  const uniqueSectors = useMemo(() => {
    if (sectors.length > 0) return sectors;
    const set = new Set(stocks.map((s) => s.sector).filter(Boolean) as string[]);
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'tr'));
  }, [sectors, stocks]);

  return (
    <AppShell>
      <div className={styles.page}>

        {/* ── Header ── */}
        <div className={styles.header}>
          <p className={styles.eyebrow}>Borsa İstanbul</p>
          <h1 className={styles.title}>
            Tüm Hisseler
            <span className={styles.titleCount}>· {loading ? '…' : `${filtered.length}/${total}`}</span>
          </h1>
        </div>

        {/* ── Toolbar ── */}
        <div className={styles.toolbar}>
          <input
            className={styles.searchInput}
            type="text"
            placeholder="Sembol veya şirket ara…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <div className={styles.pills}>
            <button
              className={`${styles.pill} ${sectorFilter === '' ? styles.pillActive : ''}`}
              onClick={() => setSectorFilter('')}
            >
              Tümü
            </button>
            {uniqueSectors.map((sec) => (
              <button
                key={sec}
                className={`${styles.pill} ${sectorFilter === sec ? styles.pillActive : ''}`}
                onClick={() => setSectorFilter(sec)}
              >
                {sec}
              </button>
            ))}
          </div>
        </div>

        {/* ── Error ── */}
        {loadError && (
          <div className={styles.errorMsg}>Hata: {loadError}</div>
        )}

        {/* ── Table ── */}
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} onClick={() => toggleSort('symbol')}>
                  Sembol <SortIcon col="symbol" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={styles.th} onClick={() => toggleSort('name')}>
                  Şirket <SortIcon col="name" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.hideMobile}`} onClick={() => toggleSort('sector')}>
                  Sektör <SortIcon col="sector" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.thRight}`} onClick={() => toggleSort('current_price')}>
                  Fiyat <SortIcon col="current_price" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.thRight}`} onClick={() => toggleSort('daily_change_pct')}>
                  Değişim <SortIcon col="daily_change_pct" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.thRight} ${styles.hideMobile}`} onClick={() => toggleSort('fundamental_score')}>
                  F/K <SortIcon col="fundamental_score" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.thRight} ${styles.hideTablet}`} onClick={() => toggleSort('market_cap')}>
                  P.Değeri <SortIcon col="market_cap" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={`${styles.th} ${styles.thRight} ${styles.hideMobile}`} onClick={() => toggleSort('volume')}>
                  Hacim <SortIcon col="volume" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className={styles.th} style={{ textAlign: 'center' }}>☆</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonRows />
              ) : (
                filtered.map((stock, index) => {
                  const isUp = (stock.daily_change_pct ?? 0) >= 0;
                  const changeColor = isUp ? 'var(--accent-green)' : 'var(--accent-red)';

                  return (
                    <tr
                      key={`${stock.symbol}-${index}`}
                      className={styles.row}
                      onClick={() => handleRowClick(stock.symbol)}
                    >
                      <td className={styles.tdSymbol}>{stock.symbol}</td>
                      <td className={styles.tdName}>{stock.name ?? '—'}</td>
                      <td className={`${styles.tdSector} ${styles.hideMobile}`}>{stock.sector ?? '—'}</td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono}`}>
                        {formatPrice(stock.current_price)}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono}`} style={{ color: changeColor }}>
                        {stock.daily_change_pct !== null
                          ? `${isUp ? '+' : ''}${stock.daily_change_pct.toFixed(2)}%`
                          : '—'}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono} ${styles.muted} ${styles.hideMobile}`}>
                        {stock.fundamental_score !== null ? stock.fundamental_score.toFixed(0) : '—'}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono} ${styles.muted} ${styles.hideTablet}`}>
                        {formatMarketCap(stock.market_cap)}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono} ${styles.muted} ${styles.hideMobile}`}>
                        {formatVolume(stock.volume)}
                      </td>
                      <td className={styles.tdStar}>☆</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>

          {!loading && filtered.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🔍</div>
              <div className={styles.emptyTitle}>Sonuç bulunamadı</div>
              <p className={styles.emptyDesc}>Arama veya filtre kriterlerinizi değiştirmeyi deneyin.</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
