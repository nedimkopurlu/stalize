'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { PriceChange, formatPrice, formatVolume } from '@/components/StockHelpers';
import {
  api,
  MarketBist100Response,
  MarketForexResponse,
  MarketGoldResponse,
  ForexPair,
  DashboardData,
  IntelligenceOverview,
  StockSummary,
  Bist100HistoryResponse,
  PortfolioPosition,
} from '@/lib/api';
import styles from './page.module.css';

const REFRESH_SECONDS = 30;

// Deterministic LCG-based mock series. Same seed → same array.
function seedSeries(seed: string, n: number, base = 9000, spread = 200): number[] {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return Array.from({ length: n }, (_, i) => {
    h = (h * 1664525 + 1013904223) >>> 0;
    const noise = ((h >>> 16) / 65535 - 0.5) * spread;
    return base + noise + (i / n) * (spread * 0.25);
  });
}

// ── Full line chart with area fill ───────────────────────────
function Bist100Chart({
  points,
  color,
  period,
  seedValues,
}: {
  points: Bist100HistoryResponse['points'];
  color: string;
  period: string;
  seedValues?: number[];
}) {
  const values = useMemo(() => {
    if ((period === '1G' || period === '1H') && seedValues && seedValues.length >= 2) {
      return seedValues;
    }
    const n = period === '1A' ? 30 : period === '3A' ? 90 : period === '1Y' ? 252 : points.length;
    return points.slice(-n).map((p) => p.close);
  }, [period, points, seedValues]);
  if (values.length < 2) return <div className={styles.chartEmpty}>Grafik için yeterli gerçek veri yok.</div>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const W = 600;
  const H = 160;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - ((v - min) / range) * (H - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const ptsStr = pts.join(' ');
  const fillPts = `0,${H} ${ptsStr} ${W},${H}`;
  const fillId = `bist-fill-${period}`;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ display: 'block', height: 160 }}>
      <defs>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill={`url(#${fillId})`} />
      <polyline points={ptsStr} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Label maps ────────────────────────────────────────────────
const FOREX_TR_LABELS: Record<string, string> = {
  'USDTRY=X': 'Dolar',
  'EURTRY=X': 'Avro',
  'GBPTRY=X': 'Sterlin',
  'CNYTRY=X': 'Çin Yuanı',
  'JPYTRY=X': 'Japon Yeni',
  'CHFTRY=X': 'İsviçre Frangı',
};

const GOLD_TR_LABELS: Record<string, string> = {
  gram: 'Gram Altın',
  ons: 'Ons Altın',
  ceyrek: 'Çeyrek Altın',
  yarim: 'Yarım Altın',
  tam: 'Tam Altın',
};
const GOLD_FORM_ORDER = ['gram', 'ons', 'ceyrek', 'yarim', 'tam'] as const;
type GoldKey = (typeof GOLD_FORM_ORDER)[number];

// ── Page ──────────────────────────────────────────────────────
export default function DashboardPage() {
  const [bist100, setBist100] = useState<MarketBist100Response | null>(null);
  const [bistHistory, setBistHistory] = useState<Bist100HistoryResponse | null>(null);
  const [bist100Loading, setBist100Loading] = useState(true);

  const [forex, setForex] = useState<MarketForexResponse | null>(null);
  const [forexLoading, setForexLoading] = useState(true);
  const [forexError, setForexError] = useState<string | null>(null);

  const [gold, setGold] = useState<MarketGoldResponse | null>(null);
  const [goldLoading, setGoldLoading] = useState(true);
  const [goldError, setGoldError] = useState<string | null>(null);

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [intel, setIntel] = useState<IntelligenceOverview | null>(null);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);

  const [countdown, setCountdown] = useState(REFRESH_SECONDS);
  const [chartPeriod, setChartPeriod] = useState<'1G' | '1H' | '1A' | '3A' | '1Y' | 'Tüm'>('1A');

  useEffect(() => {
    const fetchAll = () => {
      api
        .getMarketBist100()
        .then((d) => setBist100(d))
        .catch(() => {})
        .finally(() => setBist100Loading(false));

      api
        .getMarketBist100History(365)
        .then((d) => setBistHistory(d))
        .catch(() => setBistHistory(null));

      api
        .getMarketForex()
        .then((d) => { setForex(d); setForexError(null); })
        .catch(() => setForexError('Döviz verisi alınamadı'))
        .finally(() => setForexLoading(false));

      api
        .getMarketGold()
        .then((d) => { setGold(d); setGoldError(null); })
        .catch(() => setGoldError('Altın verisi alınamadı'))
        .finally(() => setGoldLoading(false));

      api.getDashboard().then((d) => setDashboard(d)).catch(() => {});
      api.getIntelligenceOverview(6).then((d) => setIntel(d)).catch(() => {});
      api.getPortfolioPositions().then((d) => setPositions(d)).catch(() => setPositions([]));
    };

    fetchAll();
    let secs = REFRESH_SECONDS;
    const tick = setInterval(() => {
      secs -= 1;
      if (secs <= 0) { secs = REFRESH_SECONDS; fetchAll(); }
      setCountdown(secs);
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  const bist100Up = (bist100?.daily_change_pct ?? 0) >= 0;
  const topSignal = dashboard?.top_buy?.[0] ?? null;
  const portfolioValue = positions.reduce((total, position) => {
    if (position.current_price == null) return total;
    return total + position.current_price * position.quantity;
  }, 0);

  return (
    <AppShell>
      <div className={styles.page}>

        {/* ─── Top bar ─── */}
        <div className={styles.topBar}>
          <div className={styles.searchBar}>
            <svg width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <circle cx={11} cy={11} r={8} />
              <path d="m21 21-4.3-4.3" />
            </svg>
            Hisse, sektör veya haber ara…
            <kbd className={styles.searchKbd}>⌘K</kbd>
          </div>
          <div className={styles.topBarRefresh}>
            <span className={styles.refreshDot} />
            {countdown}s
          </div>
        </div>

        {/* ─── Hero 2-col ─── */}
        <div className={styles.heroGrid}>
          {/* BIST100 */}
          <div className={styles.heroCard}>
            <div className={styles.heroCardTop}>
              <div>
                <div className={styles.heroEyebrow}>BIST 100 · Bugün</div>
                <div className={styles.heroMain}>
                  <div className={styles.heroValue}>
                    {bist100Loading ? '—' : formatPrice(bist100?.value ?? null)}
                  </div>
                  <div className={styles.heroChange}>
                    {bist100 ? <PriceChange value={bist100.daily_change_pct} /> : '—'}
                  </div>
                </div>
              </div>
              <div className={styles.periodTabs}>
                {(['1G', '1H', '1A', '3A', '1Y', 'Tüm'] as const).map((p) => (
                  <button
                    key={p}
                    className={`${styles.periodTab} ${chartPeriod === p ? styles.periodTabActive : ''}`}
                    onClick={() => setChartPeriod(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className={styles.heroChart}>
              {chartPeriod === '1G' || chartPeriod === '1H' ? (
                <Bist100Chart
                  points={bistHistory?.points ?? []}
                  color={bist100Up ? '#10b981' : '#ef4444'}
                  period={chartPeriod}
                  seedValues={seedSeries(chartPeriod, chartPeriod === '1G' ? 48 : 30, bist100?.value ?? 9000, 200)}
                />
              ) : bistHistory?.points?.length ? (
                <Bist100Chart points={bistHistory.points} color={bist100Up ? '#10b981' : '#ef4444'} period={chartPeriod} />
              ) : (
                <div className={styles.chartSkeleton} />
              )}
            </div>
            <div className={styles.heroStats}>
              <span>Son gerçek nokta: <strong>{bistHistory?.points?.at(-1)?.date ?? '—'}</strong></span>
              <span>Hacim: <strong>{bist100 ? formatVolume(bist100.volume) : '—'}</strong></span>
            </div>
          </div>

          {/* Portfolio */}
          <div className={styles.heroCard}>
            <div className={styles.heroEyebrow}>Portföyüm</div>
            <div className={styles.portfolioValue}>
              {positions.length > 0 && portfolioValue > 0 ? `₺${formatPrice(portfolioValue)}` : '—'}
            </div>
            <div className={styles.portfolioDay}>
              {positions.length > 0 ? `${positions.length} aktif pozisyon` : 'Aktif pozisyon yok.'}
            </div>
            {positions.length > 0 ? (
              <div className={styles.portfolioPositions}>
                {positions.slice(0, 5).map((position, index) => (
                  <Link key={`${position.id}-${position.symbol}-${index}`} href={`/stocks/${position.symbol}`} className={styles.portfolioPositionRow}>
                    <span>{position.symbol}</span>
                    <strong>{position.pnl_pct != null ? `${position.pnl_pct >= 0 ? '+' : ''}${position.pnl_pct.toFixed(2)}%` : '—'}</strong>
                  </Link>
                ))}
              </div>
            ) : (
              <Link href="/portfolio" className={styles.emptyLink}>Pozisyon ekle</Link>
            )}
          </div>
        </div>

        {/* ─── AI signal banner ─── */}
        {topSignal && (
          <Link href={`/stocks/${topSignal.symbol}`} className={styles.aiBanner}>
            <div className={styles.aiIcon}>✦</div>
            <div className={styles.aiBannerBody}>
              <div className={styles.aiBannerTitle}>
                <span className={styles.aiBannerLabel}>Model sinyali:</span>{' '}
                En yüksek skorlu hisse: <strong>{topSignal.symbol}</strong> ·{' '}
                {topSignal.recommendation}
              </div>
              <div className={styles.aiBannerSub}>
                {topSignal.sector} · {topSignal.name}
                {topSignal.target_price
                  ? ` · Hedef ₺${formatPrice(topSignal.target_price)}`
                  : ''}
              </div>
            </div>
            <div className={styles.aiBannerCta}>İncele →</div>
          </Link>
        )}

        {/* ─── 3-col grid ─── */}
        <div className={styles.threeCol}>
          {/* Yükselenler */}
          <div className={styles.colCard}>
            <div className={styles.colHeader}>
              <span className={styles.colTitle}>📈 En Çok Yükselenler</span>
              <Link href="/stocks" className={styles.colMore}>Tümü →</Link>
            </div>
            {dashboard?.top_gainers?.length ? (
              <StockRows stocks={dashboard.top_gainers.slice(0, 5)} />
            ) : (
              <SkeletonRows n={5} />
            )}
          </div>

          {/* Düşenler */}
          <div className={styles.colCard}>
            <div className={styles.colHeader}>
              <span className={styles.colTitle}>📉 En Çok Düşenler</span>
              <Link href="/stocks" className={styles.colMore}>Tümü →</Link>
            </div>
            {dashboard?.top_losers?.length ? (
              <StockRows stocks={dashboard.top_losers.slice(0, 5)} />
            ) : (
              <SkeletonRows n={5} />
            )}
          </div>

          {/* Haberler */}
          <div className={styles.colCard}>
            <div className={styles.colHeader}>
              <span className={styles.colTitle}>📰 Piyasa Akışı</span>
              <Link href="/intelligence" className={styles.colMore}>Tümü →</Link>
            </div>
            {intel?.feed?.length ? (
              <NewsFeed items={intel.feed.slice(0, 5)} />
            ) : (
              <SkeletonRows n={5} />
            )}
          </div>
        </div>

        {/* ─── Market data row ─── */}
        <div className={styles.marketRow}>
          <div className={styles.marketCard}>
            <div className={styles.marketCardHeader}>
              <span className={styles.marketCardTitle}>Döviz</span>
            </div>
            {forexError ? (
              <p className={styles.errText}>{forexError}</p>
            ) : !forex && forexLoading ? (
              <SkeletonRows n={4} />
            ) : (
              <ForexList pairs={forex?.pairs ?? []} />
            )}
          </div>

          <div className={styles.marketCard}>
            <div className={styles.marketCardHeader}>
              <span className={styles.marketCardTitle}>Altın</span>
            </div>
            {goldError ? (
              <p className={styles.errText}>{goldError}</p>
            ) : !gold && goldLoading ? (
              <SkeletonRows n={4} />
            ) : (
              <GoldList forms={gold?.forms ?? null} />
            )}
          </div>
        </div>

      </div>
    </AppShell>
  );
}

/* ── Sub-components ── */

function MiniSparkline({ values, up }: { values: number[]; up: boolean }) {
  if (values.length < 2) return <span style={{ display: 'inline-block', width: 40, height: 28 }} />;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const W = 40;
  const H = 28;
  const pts = values
    .map((v, i) => `${((i / (values.length - 1)) * W).toFixed(1)},${(H - ((v - min) / range) * (H - 4) - 2).toFixed(1)}`)
    .join(' ');
  const color = up ? 'var(--accent-green)' : 'var(--accent-red)';
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function StockRows({ stocks }: { stocks: StockSummary[] }) {
  return (
    <div className={styles.stockList}>
      {stocks.map((s, index) => {
        const up = (s.daily_change_pct ?? 0) >= 0;
        const sparkValues = seedSeries(s.symbol, 20, s.current_price ?? 100, Math.max(2, (s.current_price ?? 100) * 0.04));
        return (
          <Link key={`${s.symbol}-${index}`} href={`/stocks/${s.symbol}`} className={styles.stockRow}>
            <span className={styles.stockSymbol}>{s.symbol}</span>
            <span className={styles.stockName}>{s.name}</span>
            <MiniSparkline values={sparkValues} up={up} />
            <span className={styles.stockPrice}>{formatPrice(s.current_price)}</span>
            <span className={styles.stockChange} data-up={String(up)}>
              {up ? '+' : ''}
              {(s.daily_change_pct ?? 0).toFixed(2)}%
            </span>
          </Link>
        );
      })}
    </div>
  );
}

function NewsFeed({ items }: { items: IntelligenceOverview['feed'] }) {
  return (
    <div className={styles.newsList}>
      {items.map((n, i) => {
        const imp =
          (n.importance_score ?? 0) > 0.6
            ? 'high'
            : (n.importance_score ?? 0) > 0.3
            ? 'medium'
            : 'low';
        return (
          <div key={i} className={styles.newsItem}>
            <div className={styles.newsBar} data-impact={imp} />
            <div className={styles.newsBody}>
              <div className={styles.newsMeta}>
                <span>{n.publisher ?? 'Kaynak'}</span>
                {n.symbol && (
                  <span className={styles.newsTag}>{n.symbol}</span>
                )}
              </div>
              <div className={styles.newsTitle}>{n.headline}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ForexList({ pairs }: { pairs: ForexPair[] }) {
  if (pairs.length === 0)
    return <p className={styles.errText}>Veri bekleniyor…</p>;
  return (
    <div className={styles.pairList}>
      {pairs.map((p, index) => (
        <div key={`${p.symbol}-${index}`} className={styles.pairRow}>
          <span className={styles.pairLabel}>
            {FOREX_TR_LABELS[p.symbol] ?? p.name}
          </span>
          <span className={styles.pairRight}>
            <span className={styles.pairPrice}>
              ₺{formatPrice(p.rate)}
            </span>
            <PriceChange value={p.daily_change_pct} />
          </span>
        </div>
      ))}
    </div>
  );
}

function GoldList({
  forms,
}: {
  forms: MarketGoldResponse['forms'] | null;
}) {
  if (!forms)
    return <p className={styles.errText}>Veri bekleniyor…</p>;
  return (
    <div className={styles.pairList}>
      {GOLD_FORM_ORDER.map((key) => (
        <div key={key} className={styles.pairRow}>
          <span className={styles.pairLabel}>{GOLD_TR_LABELS[key]}</span>
          <span className={styles.pairRight}>
            <span className={styles.pairPrice}>
              ₺{formatPrice(forms[key as GoldKey])}
            </span>
            {/* Gold change_pct unavailable from backend (Phase 28 limitation) */}
            <PriceChange value={null} />
          </span>
        </div>
      ))}
    </div>
  );
}

function SkeletonRows({ n }: { n: number }) {
  return (
    <div className={styles.skeletonList}>
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className={`skeleton ${styles.skeletonRow}`} />
      ))}
    </div>
  );
}
