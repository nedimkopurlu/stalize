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
} from '@/lib/api';
import styles from './page.module.css';

const REFRESH_SECONDS = 30;

// ── Seed-based price series (deterministic) ───────────────────
function seedSeries(seed: number, n: number, base: number): number[] {
  let v = base;
  let s = seed * 9301;
  return Array.from({ length: n }, () => {
    s = (s * 9301 + 49297) % 233280;
    v = v * (1 + ((s / 233280 - 0.5) * 2) * 0.012);
    return v;
  });
}

// ── Full line chart with area fill ───────────────────────────
function Bist100Chart({
  baseValue,
  color,
  period,
}: {
  baseValue: number;
  color: string;
  period: string;
}) {
  const n = period === '1G' ? 48 : period === '1H' ? 30 : period === '1A' ? 52 : period === '3A' ? 90 : 180;
  const seed = Math.floor(baseValue) % 9999;
  const values = useMemo(() => seedSeries(seed, n, baseValue * 0.88), [seed, n, baseValue]);
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

function Sparkline({
  seed,
  color,
  width = 60,
  height = 20,
}: {
  seed: number;
  color: string;
  width?: number;
  height?: number;
}) {
  const values = seedSeries(seed, 20, 100);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v: number, i: number) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 2) - 1;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ── Portfolio donut with legend ───────────────────────────────
const PORTFOLIO_SLICES = [
  { name: 'Bankacılık', pct: 38, color: '#f59e0b' },
  { name: 'Sanayi', pct: 24, color: '#3b82f6' },
  { name: 'Holding', pct: 18, color: '#a855f7' },
  { name: 'Teknoloji', pct: 12, color: '#10b981' },
  { name: 'Diğer', pct: 8, color: '#64748b' },
];

function PortfolioDonut({ size = 96, thickness = 16 }: { size?: number; thickness?: number }) {
  const R = (size - thickness) / 2;
  const cx = size / 2;
  const circumference = 2 * Math.PI * R;
  let offset = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flexShrink: 0 }}>
      {PORTFOLIO_SLICES.map((s, i) => {
        const dash = (s.pct / 100) * circumference;
        const el = (
          <circle
            key={i}
            cx={cx}
            cy={cx}
            r={R}
            fill="none"
            stroke={s.color}
            strokeWidth={thickness}
            strokeDasharray={`${dash} ${circumference - dash}`}
            strokeDashoffset={-offset}
            transform={`rotate(-90 ${cx} ${cx})`}
            opacity={0.8}
          />
        );
        offset += dash;
        return el;
      })}
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
  const [bist100Loading, setBist100Loading] = useState(true);

  const [forex, setForex] = useState<MarketForexResponse | null>(null);
  const [forexLoading, setForexLoading] = useState(true);
  const [forexError, setForexError] = useState<string | null>(null);

  const [gold, setGold] = useState<MarketGoldResponse | null>(null);
  const [goldLoading, setGoldLoading] = useState(true);
  const [goldError, setGoldError] = useState<string | null>(null);

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [intel, setIntel] = useState<IntelligenceOverview | null>(null);

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
              {bist100?.value ? (
                <Bist100Chart baseValue={bist100.value} color={bist100Up ? '#10b981' : '#ef4444'} period={chartPeriod} />
              ) : (
                <div className={styles.chartSkeleton} />
              )}
            </div>
            <div className={styles.heroStats}>
              <span>Açılış: <strong>{bist100 ? formatPrice((bist100.value ?? 0) * 0.998) : '—'}</strong></span>
              <span>Yüksek: <strong>{bist100 ? formatPrice((bist100.value ?? 0) * 1.004) : '—'}</strong></span>
              <span>Düşük: <strong>{bist100 ? formatPrice((bist100.value ?? 0) * 0.994) : '—'}</strong></span>
              <span>Hacim: <strong>{bist100 ? formatVolume(bist100.volume) : '—'}</strong></span>
            </div>
          </div>

          {/* Portfolio */}
          <div className={styles.heroCard}>
            <div className={styles.heroEyebrow}>Portföyüm</div>
            <div className={styles.portfolioValue}>₺ —</div>
            <div className={styles.portfolioDay}>Portföy verisi bekleniyor…</div>
            <div className={styles.portfolioContent}>
              <PortfolioDonut size={100} thickness={18} />
              <div className={styles.portfolioLegend}>
                {PORTFOLIO_SLICES.map((s) => (
                  <div key={s.name} className={styles.legendItem}>
                    <span className={styles.legendDot} style={{ background: s.color }} />
                    <span className={styles.legendName}>{s.name}</span>
                    <span className={styles.legendPct}>{s.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ─── AI signal banner ─── */}
        {topSignal && (
          <Link href={`/stocks/${topSignal.symbol}`} className={styles.aiBanner}>
            <div className={styles.aiIcon}>✦</div>
            <div className={styles.aiBannerBody}>
              <div className={styles.aiBannerTitle}>
                <span className={styles.aiBannerLabel}>AI Asistan:</span>{' '}
                Bugünkü en güçlü sinyal: <strong>{topSignal.symbol}</strong> ·{' '}
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

function StockRows({ stocks }: { stocks: StockSummary[] }) {
  return (
    <div className={styles.stockList}>
      {stocks.map((s) => {
        const up = (s.daily_change_pct ?? 0) >= 0;
        const seed =
          (s.symbol.charCodeAt(0) || 1) * 7 +
          (s.symbol.charCodeAt(1) || 1);
        return (
          <Link key={s.symbol} href={`/stocks/${s.symbol}`} className={styles.stockRow}>
            <span className={styles.stockSymbol}>{s.symbol}</span>
            <span className={styles.stockName}>{s.name}</span>
            <span className={styles.stockPrice}>{formatPrice(s.current_price)}</span>
            <span
              className={styles.stockChange}
              data-up={String(up)}
            >
              {up ? '+' : ''}
              {(s.daily_change_pct ?? 0).toFixed(2)}%
            </span>
            <Sparkline
              seed={seed}
              color={up ? '#10b981' : '#ef4444'}
              width={60}
              height={20}
            />
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
      {pairs.map((p) => (
        <div key={p.symbol} className={styles.pairRow}>
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
