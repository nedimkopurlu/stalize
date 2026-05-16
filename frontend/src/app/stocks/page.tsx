'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import { formatPrice, formatVolume, formatMarketCap, safeLabel, safeLabelTooltip } from '@/components/StockHelpers';
import api, { StockSummary } from '@/lib/api';
import styles from './page.module.css';

// ── Types ──────────────────────────────────────────────────

type SortKey = 'symbol' | 'name' | 'sector' | 'current_price' | 'daily_change_pct' | 'fundamental_score' | 'market_cap' | 'volume';
type SortDir = 'asc' | 'desc';

// ── Helpers ────────────────────────────────────────────────

function recSafeColor(rec: string | null): string {
  if (!rec) return 'var(--text-muted)';
  if (rec === 'GÜÇLÜ AL' || rec === 'AL') return 'var(--accent-green)';
  if (rec === 'GÜÇLÜ SAT' || rec === 'SAT') return 'var(--accent-red)';
  return 'var(--accent)';
}

// Veri bütünlüğü: 3 temel bileşeni say (KARAR-02)
function componentCount(stock: StockSummary): { available: number; total: number } {
  const total = 3;
  const available = [stock.fundamental_score, stock.technical_score, stock.sentiment_score]
    .filter((v) => v !== null && v !== undefined).length;
  return { available, total };
}

// 20 günlük volatilite proxy: StockSummary'de fiyat geçmişi yok
// Volatilite için daily_change_pct kullanilir: abs(daily_change_pct) > 4 eşiği
// (günlük %4+ hareket yüksek volatilite sinyali)
function isHighDailyVolatility(stock: StockSummary): boolean {
  return stock.daily_change_pct !== null && Math.abs(stock.daily_change_pct) > 4;
}

// Stale data helpers (VERI-01, VERI-03)
function isStale(date: Date | null): boolean {
  if (!date) return false;
  return Date.now() - date.getTime() > 8 * 3600 * 1000;
}

function formatUpdateTime(date: Date | null): string {
  if (!date) return '';
  return date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

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
          {Array.from({ length: 9 }).map((__, j) => (
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
  const [latestUpdate, setLatestUpdate] = useState<Date | null>(null);
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
    api.getStocks({ sort_by: 'overall_score', limit: 200 })
      .then((res) => {
        setStocks(res.stocks);
        setTotal(res.total);
        // En son updated_at tarihini bul (VERI-01, VERI-03)
        const dates = res.stocks
          .map((s) => s.updated_at ? new Date(s.updated_at) : null)
          .filter((d): d is Date => d !== null && !isNaN(d.getTime()));
        if (dates.length > 0) {
          setLatestUpdate(new Date(Math.max(...dates.map((d) => d.getTime()))));
        }
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

        {/* ── Stale data uyarısı (VERI-03) ── */}
        {!loading && latestUpdate !== null && isStale(latestUpdate) && (
          <div className={styles.staleBanner}>
            ⚠ Veriler 8+ saat önce güncellendi — piyasa kapalı olabilir
          </div>
        )}

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
                <th className={styles.th} style={{ textAlign: 'center' }}>Görünüm</th>
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
                        {(stock.daily_change_pct ?? 0) >= 9.8 && (
                          <span className={styles.tavanBadge}>TAVAN</span>
                        )}
                        {(stock.daily_change_pct ?? 0) <= -9.8 && (
                          <span className={styles.tabanBadge}>TABAN</span>
                        )}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.hideMobile}`}>
                        <div className={styles.integrityCell}>
                          <span className={`${styles.mono} ${styles.muted}`}>
                            {stock.fundamental_score !== null ? stock.fundamental_score.toFixed(0) : '—'}
                          </span>
                          <span
                            className={styles.componentBadge}
                            title={componentCount(stock).available < componentCount(stock).total
                              ? 'Bazı bileşenler eksik; genel skor kısmi veriye dayanıyor.'
                              : 'Tüm bileşenler mevcut.'}
                            data-incomplete={componentCount(stock).available < componentCount(stock).total || undefined}
                          >
                            {componentCount(stock).available}/{componentCount(stock).total}
                          </span>
                          {isHighDailyVolatility(stock) && (
                            <span
                              className={styles.volWarn}
                              title="Yüksek volatilite — sinyaller daha az güvenilir"
                            >
                              ⚠
                            </span>
                          )}
                        </div>
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono} ${styles.muted} ${styles.hideTablet}`}>
                        {formatMarketCap(stock.market_cap)}
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} ${styles.mono} ${styles.muted} ${styles.hideMobile}`}>
                        {formatVolume(stock.volume)}
                      </td>
                      <td
                        className={styles.td}
                        style={{ textAlign: 'center' }}
                        title={safeLabelTooltip(stock.recommendation)}
                      >
                        <span style={{ fontSize: '0.72rem', color: recSafeColor(stock.recommendation) }}>
                          {safeLabel(stock.recommendation)}
                        </span>
                        {stock.data_quality_score != null && (
                          <span
                            className={`${styles.qualityBadge} ${
                              stock.data_quality_score < 50
                                ? styles.qualityLow
                                : stock.data_quality_score <= 75
                                ? styles.qualityMid
                                : styles.qualityHigh
                            }`}
                            title={
                              stock.data_quality_score < 50
                                ? "Düşük Veri Güveni: Bu hissenin temel verileri yfinance'te USD cinsinden görünüyor olabilir. Skorlar tahmini."
                                : `Veri Güven Skoru: ${Math.round(stock.data_quality_score)}/100`
                            }
                          >
                            DK: {Math.round(stock.data_quality_score)}
                          </span>
                        )}
                        {stock.liquidity_score === 'düşük' && (
                          <span className={styles.liquidityBadgeLow} title="Düşük likidite">Düşük Lik.</span>
                        )}
                        {stock.liquidity_score === 'orta' && (
                          <span className={styles.liquidityBadgeMedium} title="Orta likidite">Orta Lik.</span>
                        )}
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

        {/* ── Altbilgi — son güncelleme (VERI-01) ── */}
        {!loading && latestUpdate !== null && (
          <div className={styles.tableFooter}>
            Son güncelleme: {formatUpdateTime(latestUpdate)}
          </div>
        )}
      </div>
    </AppShell>
  );
}
