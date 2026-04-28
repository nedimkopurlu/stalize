'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import AppShell from '@/components/AppShell';
import ScoreRing from '@/components/ScoreRing';
import RecommendationBadge, { PriceChange, formatPrice, formatVolume } from '@/components/StockHelpers';
import { TerminalPageHeader, TerminalShell } from '@/components/TerminalPrimitives';
import api, { StockSummary } from '@/lib/api';
import Link from 'next/link';
import styles from './stocks.module.css';

export default function StocksPage() {
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('overall_score');
  const [filterBist30, setFilterBist30] = useState(false);
  const [filterBist100, setFilterBist100] = useState(false);
  const [filterBist250, setFilterBist250] = useState(false);
  const [filterRec, setFilterRec] = useState('');
  const [filterSector, setFilterSector] = useState('');
  const [minScore, setMinScore] = useState<number | ''>('');
  const [maxScore, setMaxScore] = useState<number | ''>('');
  const [sectors, setSectors] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Load sector list from API on mount
  useEffect(() => {
    api.getStockSectors().then((res) => setSectors(res.sectors)).catch(() => {});
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sector = params.get('sector');
    if (sector) {
      setFilterSector(sector);
    }
  }, []);

  const loadStocks = useCallback(async (pageNum: number, append: boolean) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const res = await api.getStocks({
        sort_by: sortBy,
        limit: 50,
        offset: pageNum * 50,
        search: search || undefined,
        bist30: filterBist30 || undefined,
        bist100: filterBist100 || undefined,
        bist250: filterBist250 || undefined,
        recommendation: filterRec || undefined,
        sector: filterSector || undefined,
      });
      if (append) {
        setStocks(prev => [...prev, ...res.stocks]);
      } else {
        setStocks(res.stocks);
      }
      setTotal(res.total);
      setHasMore(res.stocks.length === 50);
    } catch {
      /* */
    } finally {
      if (append) setLoadingMore(false);
      else setLoading(false);
    }
  }, [filterBist30, filterBist100, filterBist250, filterRec, filterSector, search, sortBy]);

  // Reload on filter/sort changes
  useEffect(() => {
    setPage(0);
    void loadStocks(0, false);
  }, [filterBist30, filterBist100, filterBist250, filterRec, filterSector, sortBy, loadStocks]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(0);
      void loadStocks(0, false);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, loadStocks]);

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          const nextPage = page + 1;
          setPage(nextPage);
          void loadStocks(nextPage, true);
        }
      },
      { threshold: 0.1 }
    );
    if (sentinelRef.current) observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, loading, page, loadStocks]);

  const filtered = stocks.filter((s) => {
    if (minScore !== '' && (s.overall_score ?? 0) < minScore) return false;
    if (maxScore !== '' && (s.overall_score ?? 0) > maxScore) return false;
    return true;
  });

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Hisse Radarı"
          description="BIST100 evrenini skor, sektör ve sinyal filtreleriyle daralt; karar listeni hızlıca kur."
          action={(
            <button className="btn btn-primary" onClick={() => { setPage(0); void loadStocks(0, false); }}>
              Listeyi Yenile
            </button>
          )}
        />
        {/* Filter Bar */}
        <div className={styles.filterBar}>
          <div className={styles.searchWrap}>
            <span>ARA</span>
            <input
              className="search-input"
              placeholder="Hisse ara (sembol veya isim)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className={`search-input ${styles.compactSelect} ${styles.sectorSelect}`}
            value={filterSector}
            onChange={(e) => setFilterSector(e.target.value)}
          >
            <option value="">Tüm Sektörler</option>
            {sectors.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            className={`search-input ${styles.compactSelect}`}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="overall_score">Genel Skor</option>
            <option value="technical_score">Teknik Skor</option>
            <option value="sentiment_score">Haber Skoru</option>
            <option value="daily_change_pct">Günlük Değişim</option>
            <option value="market_cap">Piyasa Değeri</option>
            <option value="volume">Hacim</option>
          </select>

          <select
            className={`search-input ${styles.compactSelect} ${styles.recommendationSelect}`}
            value={filterRec}
            onChange={(e) => setFilterRec(e.target.value)}
          >
            <option value="">Tüm Sinyaller</option>
            <option value="GÜÇLÜ AL">GÜÇLÜ AL</option>
            <option value="AL">AL</option>
            <option value="TUT">TUT</option>
            <option value="SAT">SAT</option>
            <option value="GÜÇLÜ SAT">GÜÇLÜ SAT</option>
          </select>

          {/* Score range filter */}
          <div className={styles.scoreRange}>
            <input
              type="number"
              className={`search-input ${styles.scoreInput}`}
              placeholder="Min Skor"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(e.target.value === '' ? '' : Number(e.target.value))}
            />
            <span className={styles.scoreDash}>–</span>
            <input
              type="number"
              className={`search-input ${styles.scoreInput}`}
              placeholder="Max Skor"
              min={0}
              max={100}
              value={maxScore}
              onChange={(e) => setMaxScore(e.target.value === '' ? '' : Number(e.target.value))}
            />
          </div>

          <button
            className={`btn ${filterBist30 ? 'btn-primary' : 'btn-ghost'} btn-sm`}
            onClick={() => setFilterBist30(!filterBist30)}
          >
            BIST30
          </button>
          <button
            className={`btn ${filterBist100 ? 'btn-primary' : 'btn-ghost'} btn-sm`}
            onClick={() => setFilterBist100(!filterBist100)}
          >
            BIST100
          </button>
          <button
            className={`btn ${filterBist250 ? 'btn-primary' : 'btn-ghost'} btn-sm`}
            onClick={() => setFilterBist250(!filterBist250)}
          >
            BIST250
          </button>

          <span className={styles.resultCount}>
            {stocks.length} / {total} hisse
          </span>
        </div>

        {/* Table */}
        <div className={`glass-card ${styles.tableShell}`}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Hisse</th>
                  <th>Fiyat (₺)</th>
                  <th>Değişim</th>
                  <th className="hide-mobile">Hacim</th>
                  <th className="hide-mobile">Stop-Loss</th>
                  <th className="hide-mobile">Hedef</th>
                  <th>Teknik</th>
                  <th className="hide-mobile">Temel</th>
                  <th className="hide-mobile">Haber</th>
                  <th>Genel</th>
                  <th>Sinyal</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={12}>
                        <div className="skeleton" style={{ height: 20, width: '100%' }} />
                      </td>
                    </tr>
                  ))
                ) : (
                  filtered.map((stock, idx) => (
	                    <tr key={stock.symbol} className="animate-fade-in" style={{ animationDelay: `${idx * 15}ms`, background: 'rgba(255,255,255,0.02)' }}>
	                      <td className={styles.rankCell}>
	                        {idx + 1}
	                      </td>
                      <td>
                        <Link href={`/stocks/${stock.symbol}`} className={styles.stockLink}>
                          <div className={styles.stockMeta}>
                            <span className={styles.stockSymbol}>{stock.symbol}</span>
                            <span className={styles.stockName}>
                              {stock.name?.substring(0, 28)}
                            </span>
                          </div>
                        </Link>
                      </td>
                      <td className="font-mono">{formatPrice(stock.current_price)}</td>
                      <td><PriceChange value={stock.daily_change_pct} /></td>
                      <td className="hide-mobile text-muted font-mono" title={stock.volume != null ? `Ham hacim: ${formatVolume(stock.volume)}` : undefined}>
                        {stock.volume_ratio != null ? `${stock.volume_ratio.toFixed(1)}x` : '—'}
                      </td>
                      <td className="hide-mobile text-muted font-mono">
                        {stock.stop_loss != null ? formatPrice(stock.stop_loss) : '—'}
                      </td>
                      <td className="hide-mobile text-muted font-mono">
                        {stock.target_price != null ? formatPrice(stock.target_price) : '—'}
                      </td>
	                      <td><ScoreRing score={stock.technical_score} size={36} strokeWidth={3} /></td>
	                      <td className="hide-mobile"><ScoreRing score={stock.fundamental_score} size={36} strokeWidth={3} /></td>
	                      <td className="hide-mobile"><ScoreRing score={stock.sentiment_score} size={36} strokeWidth={3} /></td>
	                      <td><ScoreRing score={stock.overall_score} size={40} strokeWidth={4} /></td>
	                      <td><RecommendationBadge recommendation={stock.recommendation} /></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div ref={sentinelRef} style={{ height: 1 }} />
        {loadingMore && (
          <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)' }}>
            Yükleniyor...
          </div>
        )}
        {!hasMore && stocks.length > 0 && (
          <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            Tüm {total} hisse yüklendi
          </div>
        )}
      </TerminalShell>
    </AppShell>
  );
}
