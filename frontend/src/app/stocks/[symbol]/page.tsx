'use client';

import React, { use, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import {
  formatPrice,
  formatVolume,
  formatMarketCap,
  formatPercentage,
  PriceChange,
} from '@/components/StockHelpers';
import api, {
  PricePoint,
  ScoreBreakdownResponse,
  StockDetail,
  StockFundamentals,
  StockPeer,
  StockPricesResponse,
  TechnicalResult,
} from '@/lib/api';
import styles from './page.module.css';

// ── SVG Line Chart ────────────────────────────────────────────

function LineChart({
  prices,
  color,
  width = 800,
  height = 200,
}: {
  prices: PricePoint[];
  color: string;
  width?: number;
  height?: number;
}) {
  if (!prices.length) return null;
  const closes = prices.map((p) => p.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const pts = closes
    .map((c, i) => {
      const x = (i / (closes.length - 1)) * width;
      const y = height - ((c - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ display: 'block' }}
    >
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ── Score Bar ────────────────────────────────────────────────

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const pct = value != null ? Math.max(0, Math.min(100, value)) : 0;
  const color =
    pct >= 65
      ? 'var(--accent-green)'
      : pct >= 40
        ? 'var(--accent)'
        : 'var(--accent-red)';

  return (
    <div className={styles.scoreBar}>
      <div className={styles.scoreBarHeader}>
        <span className={styles.scoreBarLabel}>{label}</span>
        <span className={styles.scoreBarValue} style={{ color }}>
          {value != null ? value.toFixed(0) : '—'}
        </span>
      </div>
      <div className={styles.scoreBarTrack}>
        <div
          className={styles.scoreBarFill}
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ── Signal color helper ──────────────────────────────────────

function recColor(rec: string | null): string {
  if (!rec) return 'var(--text-muted)';
  if (rec.includes('GÜÇLÜ AL') || rec === 'AL') return 'var(--accent-green)';
  if (rec.includes('GÜÇLÜ SAT') || rec === 'SAT') return 'var(--accent-red)';
  return 'var(--accent)';
}

// ── Skeleton ─────────────────────────────────────────────────

function Skeleton({ height = 16, width = '100%' }: { height?: number; width?: string | number }) {
  return (
    <div
      className={styles.skeleton}
      style={{ height, width: typeof width === 'number' ? `${width}px` : width }}
    />
  );
}

// ── Main Page ────────────────────────────────────────────────

export default function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = use(params);
  const router = useRouter();

  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [technical, setTechnical] = useState<TechnicalResult | null>(null);
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdownResponse | null>(null);
  const [fundamentals, setFundamentals] = useState<StockFundamentals | null>(null);
  const [peers, setPeers] = useState<StockPeer[]>([]);
  const [prices, setPrices] = useState<StockPricesResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [period, setPeriod] = useState('6m');

  // ── Load watchlist state ──────────────────────────────────
  useEffect(() => {
    const list = JSON.parse(localStorage.getItem('stalize-watchlist') || '[]') as string[];
    setInWatchlist(list.includes(symbol));
  }, [symbol]);

  function toggleWatchlist() {
    const list = JSON.parse(localStorage.getItem('stalize-watchlist') || '[]') as string[];
    const newList = inWatchlist ? list.filter((s) => s !== symbol) : [...list, symbol];
    localStorage.setItem('stalize-watchlist', JSON.stringify(newList));
    setInWatchlist(!inWatchlist);
  }

  // ── Parallel data load ────────────────────────────────────
  const loadStock = useCallback(async () => {
    setLoading(true);
    try {
      const [det, tech, breakdown] = await Promise.all([
        api.getStockDetail(symbol),
        api.getStockTechnical(symbol).catch(() => null),
        api.getStockScoreBreakdown(symbol).catch(() => null),
      ]);
      setDetail(det);
      setTechnical(tech);
      setScoreBreakdown(breakdown);
    } catch {
      /* non-critical */
    } finally {
      setLoading(false);
    }

    // Non-blocking secondary fetches
    api.getStockFundamentals(symbol)
      .then((f) => setFundamentals(f))
      .catch(() => null);

    api.getStockPeers(symbol)
      .then((r) => setPeers(r.peers))
      .catch(() => null);
  }, [symbol]);

  useEffect(() => {
    void loadStock();
  }, [loadStock]);

  // ── Price chart fetch ────────────────────────────────────
  const loadPrices = useCallback(async () => {
    try {
      const r = await api.getStockPrices(symbol, period);
      setPrices(r);
    } catch {
      /* */
    }
  }, [symbol, period]);

  useEffect(() => {
    void loadPrices();
  }, [loadPrices]);

  // ── Loading skeleton ──────────────────────────────────────
  if (loading) {
    return (
      <AppShell>
        <div className={styles.page}>
          {/* breadcrumb skeleton */}
          <div className={styles.breadcrumbBar}>
            <Skeleton height={14} width={120} />
          </div>
          {/* hero skeleton */}
          <section className={styles.hero}>
            <div className={styles.heroLeft}>
              <Skeleton height={12} width={200} />
              <Skeleton height={56} width="80%" />
              <Skeleton height={16} width="60%" />
              <Skeleton height={56} width={160} />
            </div>
            <div className={styles.heroRight}>
              <Skeleton height={280} width="100%" />
            </div>
          </section>
        </div>
      </AppShell>
    );
  }

  if (!detail) {
    return (
      <AppShell>
        <div className={styles.page}>
          <p className={styles.emptyMsg}>Hisse bulunamadı.</p>
        </div>
      </AppShell>
    );
  }

  const s = detail.stock;
  const bd = scoreBreakdown?.breakdown ?? null;

  // 52-week high/low from price data
  const allPrices = prices?.prices ?? detail.recent_prices ?? [];
  const highs = allPrices.map((p) => p.high).filter(Boolean);
  const lows = allPrices.map((p) => p.low).filter(Boolean);
  const high52 = highs.length ? Math.max(...highs) : null;
  const low52 = lows.length ? Math.min(...lows) : null;

  // AI confidence from overall score
  const aiConfidence = s.overall_score != null ? Math.round(s.overall_score) : null;
  const recommendation = bd?.recommendation ?? s.recommendation ?? null;

  // score components
  const techScore = s.technical_score;
  const fundScore = s.fundamental_score;
  const sentScore = s.sentiment_score;
  const momentumScore = bd?.components.find((c) => c.key === 'momentum')?.raw_score ?? null;
  const liquidityScore = bd?.components.find((c) => c.key === 'liquidity')?.raw_score ?? null;

  // chart color
  const chartPositive = (s.daily_change_pct ?? 0) >= 0;
  const chartColor = chartPositive ? 'var(--accent-green)' : 'var(--accent-red)';

  const PERIODS = [
    { key: '1d', label: '1G' },
    { key: '1wk', label: '1H' },
    { key: '1m', label: '1A' },
    { key: '3m', label: '3A' },
    { key: '6m', label: '6A' },
    { key: '1y', label: '1Y' },
    { key: '5y', label: '5Y' },
  ];

  return (
    <AppShell>
      <div className={styles.page}>

        {/* ── Breadcrumb bar ─────────────────────────────── */}
        <div className={styles.breadcrumbBar}>
          <button className={styles.backBtn} onClick={() => router.push('/')}>
            ← Genel Bakış
          </button>
          <nav className={styles.breadcrumb}>
            <span className={styles.breadcrumbItem}>Piyasalar</span>
            <span className={styles.breadcrumbSep}>›</span>
            <span className={styles.breadcrumbItem}>{s.sector || 'Sektör'}</span>
            <span className={styles.breadcrumbSep}>›</span>
            <span className={styles.breadcrumbActive}>{s.symbol}</span>
          </nav>
          <div className={styles.breadcrumbActions}>
            <button
              className={`${styles.pillBtn} ${inWatchlist ? styles.pillBtnActive : ''}`}
              onClick={toggleWatchlist}
            >
              {inWatchlist ? '★ Takipte' : '☆ Takibe Al'}
            </button>
            <Link href="#" className={styles.tradeBtn} onClick={(e) => e.preventDefault()}>
              Al / Sat
            </Link>
          </div>
        </div>

        {/* ── Hero section ──────────────────────────────── */}
        <section className={styles.hero}>
          {/* Left column */}
          <div className={styles.heroLeft}>
            <p className={styles.eyebrow}>
              {s.symbol} · {s.name} · {s.sector || 'Sektör'}
            </p>

            <h1 className={styles.heroTitle}>
              <span className={styles.heroSymbol}>{s.symbol}</span>{' '}
              <span className={styles.heroName}>{s.name}</span>
            </h1>

            <p className={styles.heroDesc}>
              {s.sector ? `${s.sector} sektöründe faaliyet gösteren` : ''} {s.name},{' '}
              BIST&apos;te işlem gören önemli hisseler arasında yer almaktadır.{' '}
              {aiConfidence != null && recommendation ? (
                <>
                  AI modelimiz bu hisseyi{' '}
                  <span className={styles.heroHighlight}>
                    %{aiConfidence} güvenle {recommendation}
                  </span>{' '}
                  olarak işaretliyor.
                </>
              ) : null}
            </p>

            <div className={styles.heroPrice}>
              <span className={styles.heroPriceValue}>
                {s.current_price != null ? formatPrice(s.current_price) : '—'}
                <span className={styles.heroCurrency}> ₺</span>
              </span>
              <PriceChange value={s.daily_change_pct} />
            </div>
          </div>

          {/* Right column — AI Score Card */}
          <div className={styles.heroRight}>
            <div className={styles.scoreCard}>
              <div className={styles.scoreCardHeader}>
                <span className={styles.scoreCardIcon}>✦</span>
                <span className={styles.scoreCardTitle}>AI Skor Kartı</span>
              </div>

              <div className={styles.scoreCardSignal}>
                <span
                  className={styles.signalLabel}
                  style={{ color: recColor(recommendation) }}
                >
                  {recommendation ?? 'VERİ YOK'}
                </span>
                {s.overall_score != null && (
                  <span className={styles.signalScore}>{s.overall_score.toFixed(1)}</span>
                )}
              </div>

              <div className={styles.scoreBars}>
                <ScoreBar label="Teknik" value={techScore} />
                <ScoreBar label="Temel" value={fundScore} />
                <ScoreBar label="Sentiment" value={sentScore} />
                <ScoreBar label="Momentum" value={momentumScore} />
                <ScoreBar label="Likidite" value={liquidityScore} />
              </div>

              <div className={styles.scoreCardDivider} />

              <div className={styles.scoreCardRows}>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>12 ay hedef</span>
                  <span className={styles.scoreCardRowValue}>
                    {technical?.target_price != null
                      ? `${formatPrice(technical.target_price)} ₺`
                      : s.target_price != null
                        ? `${formatPrice(s.target_price)} ₺`
                        : '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Yukarı potansiyel</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-green)' }}>
                    {(() => {
                      const tp = technical?.target_price ?? s.target_price ?? null;
                      const cp = s.current_price;
                      if (tp && cp && cp > 0) {
                        const pct = ((tp - cp) / cp) * 100;
                        return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
                      }
                      return '—';
                    })()}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Stop-loss önerisi</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-red)' }}>
                    {technical?.stop_loss != null
                      ? `${formatPrice(technical.stop_loss)} ₺`
                      : s.stop_loss != null
                        ? `${formatPrice(s.stop_loss)} ₺`
                        : '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Price chart section ─────────────────────── */}
        <section className={styles.chartSection}>
          <div className={styles.chartCard}>
            <div className={styles.chartCardHeader}>
              <div className={styles.periodSelector}>
                {PERIODS.map((p) => (
                  <button
                    key={p.key}
                    className={`${styles.periodBtn} ${period === p.key ? styles.periodBtnActive : ''}`}
                    onClick={() => setPeriod(p.key)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <span className={styles.chartTypeLabel}>Çizgi</span>
            </div>

            <div className={styles.chartArea}>
              {allPrices.length > 0 ? (
                <LineChart prices={allPrices} color={chartColor} height={200} />
              ) : (
                <div className={styles.chartEmpty}>Grafik verisi yükleniyor...</div>
              )}
            </div>

            <div className={styles.chartStats}>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>52H Yüksek</span>
                <span className={styles.chartStatValue}>
                  {high52 != null ? `${formatPrice(high52)} ₺` : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>52H Düşük</span>
                <span className={styles.chartStatValue}>
                  {low52 != null ? `${formatPrice(low52)} ₺` : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>F/K</span>
                <span className={styles.chartStatValue}>
                  {fundamentals?.pe_ratio != null ? fundamentals.pe_ratio.toFixed(1) : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>Piyasa Değeri</span>
                <span className={styles.chartStatValue}>{formatMarketCap(s.market_cap)}</span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>Hacim</span>
                <span className={styles.chartStatValue}>{formatVolume(s.volume)}</span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>Sektör</span>
                <span className={styles.chartStatValue}>{s.sector || '—'}</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── Temel Analiz tablosu ────────────────────── */}
        <section className={styles.fundSection}>
          <h2 className={styles.sectionTitle}>Temel Analiz</h2>
          <div className={styles.fundGrid}>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>F/K</span>
              <span className={styles.fundValue}>
                {fundamentals?.pe_ratio != null ? fundamentals.pe_ratio.toFixed(1) : '—'}
              </span>
            </div>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>PD/DD</span>
              <span className={styles.fundValue}>
                {fundamentals?.pb_ratio != null ? fundamentals.pb_ratio.toFixed(2) : '—'}
              </span>
            </div>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>ROE</span>
              <span className={styles.fundValue}>
                {fundamentals?.roe != null ? formatPercentage(fundamentals.roe) : '—'}
              </span>
            </div>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>Net Marj</span>
              <span className={styles.fundValue}>
                {fundamentals?.net_margin != null ? formatPercentage(fundamentals.net_margin) : '—'}
              </span>
            </div>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>Borç/Özkaynak</span>
              <span className={styles.fundValue}>
                {fundamentals?.debt_to_equity != null
                  ? fundamentals.debt_to_equity.toFixed(2)
                  : '—'}
              </span>
            </div>
            <div className={styles.fundItem}>
              <span className={styles.fundLabel}>Temel Skor</span>
              <span
                className={styles.fundValue}
                style={{
                  color:
                    fundamentals?.fundamental_score != null
                      ? recColor(
                          fundamentals.fundamental_score >= 65
                            ? 'AL'
                            : fundamentals.fundamental_score >= 40
                              ? 'TUT'
                              : 'SAT',
                        )
                      : undefined,
                }}
              >
                {fundamentals?.fundamental_score != null
                  ? fundamentals.fundamental_score.toFixed(1)
                  : '—'}
              </span>
            </div>
          </div>
        </section>

        {/* ── Benzer hisseler ──────────────────────────── */}
        {peers.length > 0 && (
          <section className={styles.peersSection}>
            <h2 className={styles.sectionTitle}>Benzer Hisseler</h2>
            <div className={styles.peersCard}>
              <table className={styles.peersTable}>
                <thead>
                  <tr>
                    <th className={styles.peersTh}>Hisse</th>
                    <th className={styles.peersTh}>Fiyat</th>
                    <th className={styles.peersTh}>F/K</th>
                    <th className={styles.peersTh}>%</th>
                  </tr>
                </thead>
                <tbody>
                  {peers.map((peer) => (
                    <tr key={peer.symbol} className={styles.peersTr}>
                      <td className={styles.peersTd}>
                        <Link href={`/stocks/${peer.symbol}`} className={styles.peerLink}>
                          <span className={styles.peerSymbol}>{peer.symbol}</span>
                          {peer.name && (
                            <span className={styles.peerName}>{peer.name}</span>
                          )}
                        </Link>
                      </td>
                      <td className={`${styles.peersTd} ${styles.mono}`}>
                        {peer.current_price != null
                          ? `${formatPrice(peer.current_price)} ₺`
                          : '—'}
                      </td>
                      <td className={`${styles.peersTd} ${styles.mono}`}>
                        {peer.overall_score != null
                          ? peer.overall_score.toFixed(1)
                          : '—'}
                      </td>
                      <td className={styles.peersTd}>
                        {peer.daily_change_pct != null ? (
                          <span
                            style={{
                              color:
                                peer.daily_change_pct >= 0
                                  ? 'var(--accent-green)'
                                  : 'var(--accent-red)',
                              fontFamily: 'monospace',
                              fontSize: '0.85rem',
                            }}
                          >
                            {peer.daily_change_pct >= 0 ? '+' : ''}
                            {peer.daily_change_pct.toFixed(2)}%
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
