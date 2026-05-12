'use client';

import React, { use, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import {
  formatPrice,
  formatVolume,
  formatMarketCap,
} from '@/components/StockHelpers';
import api, {
  InvestmentDecision,
  PricePoint,
  ScoreBreakdownResponse,
  StockAnalysisResponse,
  StockDetail,
  StockFundamentals,
  StockNewsItem,
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
      const x = closes.length === 1 ? width / 2 : (i / (closes.length - 1)) * width;
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

function PlanMetric({
  label,
  value,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  tone?: 'success' | 'danger';
}) {
  return (
    <div className={styles.planMetric}>
      <span>{label}</span>
      <strong data-tone={tone}>{value}</strong>
    </div>
  );
}

function NewsRow({ item }: { item: StockNewsItem }) {
  const content = (
    <>
      <div className={styles.newsRowMeta}>
        <span>{formatCompactDate(item.published_at)}</span>
        <span>{item.source || 'Kaynak yok'}</span>
        <span data-sentiment={item.sentiment_label || 'neutral'}>{sentimentLabel(item)}</span>
      </div>
      <strong>{item.title}</strong>
      {item.summary && <p>{item.summary}</p>}
    </>
  );

  if (item.url) {
    return (
      <a className={styles.stockNewsRow} href={item.url} target="_blank" rel="noreferrer">
        {content}
      </a>
    );
  }

  return <div className={styles.stockNewsRow}>{content}</div>;
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

// ── Safe label mapping (KARAR-01) ─────────────────────────
const SAFE_LABEL_MAP: Record<string, string> = {
  'GÜÇLÜ AL': 'Yüksek Öncelikli İzleme',
  'AL': 'Pozitif Görünüm',
  'TUT': 'Nötr İzleme',
  'SAT': 'Zayıflayan Görünüm',
  'GÜÇLÜ SAT': 'Riskli Görünüm',
};

const SAFE_LABEL_TOOLTIP: Record<string, string> = {
  'GÜÇLÜ AL': 'Teknik ve temel göstergeler güçlü; yakından takip edilebilir.',
  'AL': 'Göstergeler genel olarak olumlu; dikkatli değerlendirilebilir.',
  'TUT': 'Karma sinyaller; net yön için bekleme önerilir.',
  'SAT': 'Göstergeler baskı altında; dikkatli olunmalı.',
  'GÜÇLÜ SAT': 'Yüksek risk sinyalleri mevcut; değerlendirme önerilmez.',
};

function safeLabel(rec: string | null): string {
  if (!rec) return '—';
  return SAFE_LABEL_MAP[rec] ?? rec;
}

function safeLabelTooltip(rec: string | null): string {
  if (!rec) return '';
  return SAFE_LABEL_TOOLTIP[rec] ?? '';
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

// ── Chart period change delta ─────────────────────────────────

function getPeriodDelta(prices: PricePoint[]): string {
  if (prices.length < 2) return '';
  const first = prices[0].close;
  const last = prices[prices.length - 1].close;
  if (!first) return '';
  const pct = ((last - first) / first) * 100;
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
}

// ── Contextual hero tagline ───────────────────────────────────

function getScoreReasonRows(breakdown: ScoreBreakdownResponse['breakdown'] | null) {
  if (!breakdown) return [];
  return breakdown.components.filter((component) => component.reason).slice(0, 6);
}

function formatFinancialPct(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  return `${(value * 100).toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

function formatSignedPct(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatCompactDate(value: string | null | undefined) {
  if (!value) return 'Tarih yok';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function decisionPrimaryLabel(decision: InvestmentDecision | null, recommendation: string | null) {
  if (!decision) {
    if (!recommendation) return 'İZLE';
    if (recommendation.includes('AL')) return 'AL';
    if (recommendation.includes('SAT')) return 'UZAK DUR';
    return 'İZLE';
  }
  if (decision.action === 'strong_buy' || decision.action === 'buy') return 'AL';
  if (decision.action === 'reduce' || decision.action === 'exit') return 'UZAK DUR';
  return 'İZLE';
}

function decisionToneClass(label: string) {
  if (label === 'AL') return styles.decisionBuy;
  if (label === 'UZAK DUR') return styles.decisionAvoid;
  return styles.decisionWatch;
}

function riskLabel(value: string | null | undefined) {
  if (value === 'low') return 'Düşük';
  if (value === 'medium') return 'Orta';
  if (value === 'high') return 'Yüksek';
  return '—';
}

function trendLabel(value: string | null | undefined) {
  const map: Record<string, string> = {
    bullish: 'Yükselen',
    constructive: 'Yapıcı',
    neutral: 'Nötr',
    weak: 'Zayıf',
    bearish: 'Düşen',
    unknown: 'Belirsiz',
  };
  return value ? map[value] ?? value : '—';
}

function horizonLabel(value: string | null | undefined) {
  if (value === 'swing_2_8_weeks') return '2-8 hafta';
  return value || '—';
}

function sentimentLabel(item: StockNewsItem) {
  if (item.sentiment_label === 'positive') return 'Olumlu';
  if (item.sentiment_label === 'negative') return 'Olumsuz';
  if (item.sentiment_label === 'neutral') return 'Nötr';
  return item.sentiment_score != null ? formatSignedPct(item.sentiment_score * 100) : 'Etki yok';
}

function indicatorValue(value: number | null | undefined, suffix = '', digits = 2) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  return `${value.toLocaleString('tr-TR', { minimumFractionDigits: digits, maximumFractionDigits: digits })}${suffix}`;
}

function formatScoreNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  return value.toFixed(digits);
}

function marketUniverseLabel(stock: StockDetail['stock']) {
  if (stock.is_bist30) return 'BIST 30';
  if (stock.is_bist100) return 'BIST 100';
  if (stock.is_bist250) return 'BIST 250';
  return stock.market_tier ? `BIST · ${stock.market_tier}` : 'BIST';
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
  const [decision, setDecision] = useState<InvestmentDecision | null>(null);
  const [news, setNews] = useState<StockNewsItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [chartError, setChartError] = useState<string | null>(null);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [period, setPeriod] = useState('6m');
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);

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

  async function handleAnalyze() {
    if (analysis !== null || analyzeLoading) return; // LLM-02: session cache guard
    setAnalyzeLoading(true);
    try {
      const result: StockAnalysisResponse = await api.analyzeStock(symbol);
      setAnalysis(result.analysis);
    } catch {
      setAnalysis('Analiz alınamadı. Lütfen tekrar deneyin.');
    } finally {
      setAnalyzeLoading(false);
    }
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

    api.getStockDecision(symbol, 100000, 1, false)
      .then((r) => setDecision(r))
      .catch(() => setDecision(null));

    api.getStockNews(symbol, 50)
      .then((r) => setNews(r.items))
      .catch(() => setNews([]));
  }, [symbol]);

  useEffect(() => {
    void loadStock();
  }, [loadStock]);

  // ── Price chart fetch ────────────────────────────────────
  const loadPrices = useCallback(async () => {
    setChartError(null);
    try {
      const r = await api.getStockPrices(symbol, period);
      setPrices(r);
    } catch {
      setChartError('Grafik verisi alınamadı.');
    }
  }, [symbol, period]);

  useEffect(() => {
    void loadPrices();
  }, [loadPrices]);

  // ── Loading skeleton ──────────────────────────────────────
  if (loading) {
    return (
      <AppShell>
        <div className={styles.editorialPage}>
          <div className={styles.topNav}>
            <Skeleton height={14} width={160} />
            <Skeleton height={14} width={200} />
            <Skeleton height={32} width={180} />
          </div>
          <section className={styles.hero}>
            <div className={styles.heroLeft}>
              <Skeleton height={12} width={240} />
              <Skeleton height={64} width="80%" />
              <Skeleton height={16} width="70%" />
              <Skeleton height={64} width={180} />
            </div>
            <div className={styles.heroRight}>
              <Skeleton height={320} width="100%" />
            </div>
          </section>
        </div>
      </AppShell>
    );
  }

  if (!detail) {
    return (
      <AppShell>
        <div className={styles.editorialPage}>
          <p className={styles.emptyMsg}>Hisse bulunamadı.</p>
        </div>
      </AppShell>
    );
  }

  const s = detail.stock;
  const bd = scoreBreakdown?.breakdown ?? null;

  // Current period high/low from loaded price data
  const allPrices = prices?.prices ?? detail.recent_prices ?? [];
  const latestPoint = allPrices.at(-1) ?? null;
  const highs = allPrices.map((p) => p.high).filter((value) => Number.isFinite(value));
  const lows = allPrices.map((p) => p.low).filter((value) => Number.isFinite(value));
  const high52 = highs.length ? Math.max(...highs) : null;
  const low52 = lows.length ? Math.min(...lows) : null;

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

  const scoreReasonRows = getScoreReasonRows(bd);
  const periodDelta = getPeriodDelta(allPrices);

  // Volatilite uyarısı: son 20 günlük fiyat değişimi >%15 (KARAR-03)
  const volatilityAlert = (() => {
    const last20 = allPrices.slice(-20);
    if (last20.length < 2) return false;
    const first = last20[0].close;
    const last = last20[last20.length - 1].close;
    if (!first || !last) return false;
    return Math.abs((last - first) / first) * 100 > 15;
  })();

  // Veri bütünlüğü: kaç bileşen mevcut (KARAR-02)
  const totalComponentCount = bd?.summary ? (bd.summary.available_component_count + bd.summary.missing_component_count) : null;
  const availableComponentCount = bd?.summary?.available_component_count ?? null;

  // target price & upside potential
  const targetPrice = technical?.target_price ?? s.target_price ?? null;
  const stopLoss = technical?.stop_loss ?? s.stop_loss ?? null;
  const upsidePct = (() => {
    if (targetPrice && s.current_price && s.current_price > 0) {
      const pct = ((targetPrice - s.current_price) / s.current_price) * 100;
      if (!Number.isFinite(pct)) return null;
      return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
    }
    return null;
  })();
  const primaryDecision = decisionPrimaryLabel(decision, recommendation);
  const entryLow = decision?.entry_zone.low ?? (s.current_price != null ? s.current_price * 0.985 : null);
  const entryHigh = decision?.entry_zone.high ?? (s.current_price != null ? s.current_price * 1.015 : null);
  const planStop = decision?.stop_loss ?? stopLoss;
  const planTarget = decision?.target_price ?? targetPrice;
  const planRiskReward = decision?.risk_reward ?? null;
  const thesisRows = decision?.thesis?.length
    ? decision.thesis
    : scoreReasonRows.map((row) => row.reason).slice(0, 3);
  const watchRows = decision?.watch_items?.length
    ? decision.watch_items
    : ['BIST100 genel yönü', 'hacim teyidi', 'haber/KAP akışı'];
  const riskRows = [
    decision?.invalidation,
    fundamentals?.debt_to_equity != null && fundamentals.debt_to_equity > 2
      ? 'Borç/özkaynak oranı yüksek; faiz ve kur şoklarına duyarlılık artabilir.'
      : null,
    (s.fundamental_score ?? 50) < 45
      ? 'Temel skor zayıf; teknik görünüm tek başına yeterli olmayabilir.'
      : null,
    (s.technical_score ?? 50) < 45
      ? 'Teknik skor zayıf; fiyat planı teyit bekliyor.'
      : null,
  ].filter(Boolean) as string[];
  const technicalRows = [
    {
      label: 'RSI 14',
      value: indicatorValue(technical?.indicators.rsi_14 ?? latestPoint?.rsi_14, '', 1),
      note: '30 altı aşırı satım, 70 üstü aşırı alım bölgesi.',
    },
    {
      label: 'MACD',
      value: indicatorValue(technical?.indicators.macd ?? latestPoint?.macd, '', 2),
      note: 'Sinyal çizgisi üstünde kalması momentum teyidi verir.',
    },
    {
      label: 'MACD Sinyal',
      value: indicatorValue(technical?.indicators.macd_signal ?? latestPoint?.macd_signal, '', 2),
      note: 'MACD ile kesişim yön değişimini gösterir.',
    },
    {
      label: 'SMA 50',
      value: latestPoint?.sma_50 != null ? `₺${formatPrice(latestPoint.sma_50)}` : indicatorValue(technical?.indicators.sma_50, ' TL', 2),
      note: 'Orta vadeli trend filtresi.',
    },
    {
      label: 'SMA 200',
      value: latestPoint?.sma_200 != null ? `₺${formatPrice(latestPoint.sma_200)}` : indicatorValue(technical?.indicators.sma_200, ' TL', 2),
      note: 'Ana trend filtresi.',
    },
    {
      label: 'ATR 14',
      value: latestPoint?.atr_14 != null ? indicatorValue(latestPoint.atr_14, '', 2) : '—',
      note: 'Stop mesafesini belirlerken volatilite ölçüsü.',
    },
    {
      label: 'Destek',
      value: technical?.support != null ? `₺${formatPrice(technical.support)}` : '—',
      note: 'Fiyatın tutunması beklenen bölge.',
    },
    {
      label: 'Direnç',
      value: technical?.resistance != null ? `₺${formatPrice(technical.resistance)}` : '—',
      note: 'Kâr alma veya kırılım teyidi bölgesi.',
    },
  ];
  const fundamentalRows = [
    { label: 'F/K', value: formatScoreNumber(fundamentals?.pe_ratio), note: 'Kâr çarpanı' },
    { label: 'PD/DD', value: formatScoreNumber(fundamentals?.pb_ratio, 2), note: 'Defter değeri çarpanı' },
    { label: 'FD/FAVÖK', value: formatScoreNumber(fundamentals?.ev_ebitda), note: 'Operasyonel değerleme' },
    { label: 'ROE', value: formatFinancialPct(fundamentals?.roe), note: 'Özkaynak kârlılığı' },
    { label: 'Net Marj', value: formatFinancialPct(fundamentals?.net_margin), note: 'Kârlılık kalitesi' },
    { label: 'Borç/Özkaynak', value: formatScoreNumber(fundamentals?.debt_to_equity, 2), note: 'Bilanço riski' },
    { label: 'Temel Skor', value: formatScoreNumber(fundamentals?.fundamental_score), note: 'Modelin temel analiz notu' },
  ];

  return (
    <AppShell>
      <div className={styles.editorialPage}>

        {/* ── Top nav bar ──────────────────────────────────── */}
        <div className={styles.topNav}>
          <button className={styles.backBtn} onClick={() => router.back()}>
            ← Geri
          </button>
          <nav className={styles.breadcrumb}>
            <span className={styles.breadcrumbItem}>Piyasalar</span>
            <span className={styles.breadcrumbSep}>›</span>
            <span className={styles.breadcrumbItem}>{s.sector || 'Sektör'}</span>
            <span className={styles.breadcrumbSep}>›</span>
            <span className={styles.breadcrumbActive}>{s.symbol}</span>
          </nav>
          <div className={styles.navActions}>
            <button
              className={`${styles.watchlistBtn} ${inWatchlist ? styles.watchlistBtnActive : ''}`}
              onClick={toggleWatchlist}
            >
              {inWatchlist ? '★' : '☆'} {inWatchlist ? 'Takipte' : 'Takibe Al'}
            </button>
          </div>
        </div>

        {/* ── Hero section ──────────────────────────────────── */}
        <section className={styles.hero}>
          {/* Left column */}
          <div className={styles.heroLeft}>
            <p className={styles.eyebrow}>
              {s.symbol} · {s.name} · {marketUniverseLabel(s)}
            </p>

            <h1 className={styles.heroTitle}>
              <span className={styles.heroTitleLine}>{s.symbol}</span>
              <br />
              <em className={styles.heroSymbolItalic}>{s.name}</em>
            </h1>

            <p className={styles.heroDesc}>
              {s.sector ? `${s.sector} sektöründe sınıflandırılıyor. ` : ''}
              {primaryDecision ? (
                <>
                  Güncel işlem kararı{' '}
                  <span className={styles.confidenceBadge}>
                    {primaryDecision}
                  </span>{' '}
                  olarak okunuyor; gerekçe teknik, temel ve haber akışında aşağıda açılıyor.
                </>
              ) : 'Bu hisse için güncel model sinyali yok.'}
            </p>

            <div className={styles.heroPrice}>
              <div className={styles.heroPriceBlock}>
                <div className={styles.heroPriceLabel}>Son Fiyat</div>
                <div className={styles.heroPriceValue}>
                  ₺{s.current_price != null ? formatPrice(s.current_price) : '—'}
                </div>
              </div>
              {s.daily_change_pct != null && (
                <div className={styles.heroPriceChange}>
                  <span
                    className={styles.heroPriceChangePct}
                    style={{ color: chartPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}
                  >
                    {formatSignedPct(s.daily_change_pct)}
                  </span>
                  <span className={styles.heroPriceChangeDate}>Bugün · itibarıyla</span>
                </div>
              )}
            </div>

            {/* Quick stats row — fills the vertical gap in heroLeft */}
            <div className={styles.heroQuickStats}>
              {high52 != null && (
                <div className={styles.heroQuickStat}>
                  <span className={styles.heroQuickStatLabel}>Dönem Yüksek</span>
                  <span className={styles.heroQuickStatValue}>₺{formatPrice(high52)}</span>
                </div>
              )}
              {low52 != null && (
                <div className={styles.heroQuickStat}>
                  <span className={styles.heroQuickStatLabel}>Dönem Düşük</span>
                  <span className={styles.heroQuickStatValue}>₺{formatPrice(low52)}</span>
                </div>
              )}
              {s.market_cap != null && (
                <div className={styles.heroQuickStat}>
                  <span className={styles.heroQuickStatLabel}>Piyasa Değeri</span>
                  <span className={styles.heroQuickStatValue}>{formatMarketCap(s.market_cap)}</span>
                </div>
              )}
              {s.volume != null && (
                <div className={styles.heroQuickStat}>
                  <span className={styles.heroQuickStatLabel}>Hacim</span>
                  <span className={styles.heroQuickStatValue}>{formatVolume(s.volume)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Right column — AI Score Card */}
          <div className={styles.heroRight}>
            <div className={styles.scoreCard}>
              <div className={styles.scoreCardHeader}>
                <div className={styles.scoreCardIconWrap}>
                  <span className={styles.scoreCardIcon}>✦</span>
                </div>
                <span className={styles.scoreCardTitle}>AI Karar Kartı</span>
              </div>

              <div className={styles.scoreCardSignal}>
                <div>
                  <div className={styles.signalLabelSmall}>Karar</div>
                  <div
                    className={styles.signalLabel}
                    style={{ color: recColor(recommendation) }}
                    title={safeLabelTooltip(recommendation)}
                  >
                    {safeLabel(recommendation)}
                  </div>
                </div>
                {s.overall_score != null && (
                  <span className={styles.signalScore}>{formatScoreNumber(s.overall_score)}</span>
                )}
              </div>

              <div className={styles.scoreBars}>
                <ScoreBar label="Teknik" value={techScore} />
                <ScoreBar label="Temel" value={fundScore} />
                <ScoreBar label="Sentiment" value={sentScore} />
                <ScoreBar label="Momentum" value={momentumScore} />
                <ScoreBar label="Likidite" value={liquidityScore} />
              </div>

              {availableComponentCount !== null && totalComponentCount !== null && (
                <div className={styles.componentIntegrity}>
                  <span
                    title={availableComponentCount < totalComponentCount
                      ? 'Bazı bileşenler eksik; ağırlıklar mevcut veriye göre yeniden dağıtıldı.'
                      : 'Tüm bileşenler eksiksiz mevcut.'}
                  >
                    {availableComponentCount < totalComponentCount ? '⚠ ' : ''}
                    {availableComponentCount}/{totalComponentCount} bileşen mevcut
                  </span>
                  {volatilityAlert && (
                    <span
                      className={styles.volatilityWarning}
                      title="Yüksek volatilite — sinyaller daha az güvenilir"
                    >
                      ⚠ Yüksek volatilite
                    </span>
                  )}
                </div>
              )}

              <div className={styles.scoreCardDivider} />

              <div className={styles.scoreCardRows}>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Güven skoru</span>
                  <span className={styles.scoreCardRowValue}>
                    {decision?.confidence != null ? `${decision.confidence}/100` : '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Teknik hedef</span>
                  <span className={styles.scoreCardRowValue}>
                    {planTarget != null ? `₺${formatPrice(planTarget)}` : '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Teknik potansiyel</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-green)' }}>
                    {upsidePct ?? '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>ATR stop seviyesi</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-red)' }}>
                    {planStop != null ? `₺${formatPrice(planStop)}` : '—'}
                  </span>
                </div>
              </div>

              {/* ── Analiz Et ─────────────────────────────────── */}
              <div className={styles.scoreCardDivider} />
              <button
                className={styles.analyzeBtn}
                onClick={handleAnalyze}
                disabled={analyzeLoading || analysis !== null}
              >
                {analyzeLoading ? 'Analiz ediliyor...' : analysis !== null ? 'Analiz Tamamlandı' : '✦ AI ile analiz et'}
              </button>
              {analysis !== null && (
                <div className={styles.analyzePanel}>
                  <p className={styles.analyzeText}>{analysis}</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── Score breakdown section ──────────────────────── */}
        {bd && bd.components.length > 0 && (
          <section className={styles.breakdownSection}>
            <h2 className={styles.breakdownTitle}>Skor Dökümü</h2>
            <p className={styles.breakdownSubtitle}>
              Her bileşenin genel skora katkısı — toplam 100 üzerinden
            </p>

            {bd.summary.missing_component_count > 0 && (
              <div className={styles.breakdownMissingAlert}>
                <span>⚠</span>
                <span>Eksik veri — ağırlık yeniden dağıtıldı</span>
              </div>
            )}

            <div className={styles.breakdownBars}>
              {bd.components.map((comp) => {
                const pct = Math.max(0, Math.min(100, comp.raw_score ?? 0));
                const katkiPct = Math.round(comp.normalized_weight * 100);
                const barColor =
                  pct >= 65 ? 'var(--accent-green)'
                  : pct >= 40 ? 'var(--accent)'
                  : 'var(--accent-red)';

                const labelMap: Record<string, string> = {
                  fundamental_score: 'Temel',
                  technical_score: 'Teknik',
                  sentiment_score: 'Haber',
                  company_event_score: 'Şirket Olayı',
                  macro_regime_score: 'Makro Rejim',
                  risk_overlay_score: 'Risk Katmanı',
                };
                const displayLabel = labelMap[comp.key] ?? comp.label;

                return (
                  <div key={comp.key} className={styles.breakdownBar} title={comp.reason}>
                    <div className={styles.breakdownBarHeader}>
                      <span className={styles.breakdownBarLabel}>{displayLabel}</span>
                      <span className={styles.breakdownBarMeta}>
                        <strong style={{ color: barColor }}>{comp.raw_score != null ? comp.raw_score.toFixed(0) : '—'}</strong>
                        {' '}
                        <span className={styles.breakdownBarKatki}>— %{katkiPct} katkı</span>
                      </span>
                    </div>
                    <div className={styles.breakdownBarTrack}>
                      <div
                        className={styles.breakdownBarFill}
                        style={{ width: `${pct}%`, background: barColor }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <p className={styles.breakdownNote}>
              Skor, mevcut bileşenlerin normalize edilmiş ağırlıklı ortalamasıdır. Eksik bileşen varsa ağırlıklar yeniden dağıtılır.
            </p>
          </section>
        )}

        {/* ── Investment thesis ───────────────────────────── */}
        <section className={styles.thesisSection}>
          <article className={styles.tradePlanCard}>
            <div className={styles.cardHeaderLine}>
              <div>
                <div className={styles.sectionEyebrow}>Yatırım Kararı</div>
                <h2>Neyi neden alayım?</h2>
              </div>
              <span className={`${styles.actionPill} ${decisionToneClass(primaryDecision)}`}>
                {primaryDecision}
              </span>
            </div>
            <div className={styles.planMetrics}>
              <PlanMetric
                label="Giriş bölgesi"
                value={entryLow != null && entryHigh != null ? `₺${formatPrice(entryLow)} - ₺${formatPrice(entryHigh)}` : '—'}
              />
              <PlanMetric label="Stop" value={planStop != null ? `₺${formatPrice(planStop)}` : '—'} tone="danger" />
              <PlanMetric label="Hedef" value={planTarget != null ? `₺${formatPrice(planTarget)}` : '—'} tone="success" />
              <PlanMetric label="Risk/ödül" value={formatScoreNumber(planRiskReward, 2)} />
              <PlanMetric label="Zaman ufku" value={horizonLabel(decision?.time_horizon)} />
              <PlanMetric label="Risk" value={riskLabel(decision?.risk_level)} />
              <PlanMetric label="Trend" value={trendLabel(decision?.signals.trend)} />
            </div>
            <div className={styles.positionStrip}>
              <span>Pozisyon önerisi</span>
              <strong>
                {decision
                  ? `${decision.position_size.shares} adet · ₺${formatPrice(decision.position_size.estimated_exposure)} · portföyün %${formatScoreNumber(decision.position_size.estimated_exposure_pct, 2)}`
                  : 'Karar motoru bekleniyor'}
              </strong>
            </div>
          </article>

          <article className={styles.reasonCard}>
            <div className={styles.sectionEyebrow}>Alma gerekçesi</div>
            <h2>Tez</h2>
            <ul className={styles.cleanList}>
              {thesisRows.length ? thesisRows.slice(0, 5).map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              )) : <li>Henüz yeterli tez verisi yok.</li>}
            </ul>
          </article>

          <article className={styles.reasonCard}>
            <div className={styles.sectionEyebrow}>Ters senaryo</div>
            <h2>Nerede vazgeçerim?</h2>
            <ul className={styles.cleanList}>
              {riskRows.length ? riskRows.slice(0, 5).map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              )) : <li>Belirgin ek risk yok; stop ve haber akışı izlenmeli.</li>}
            </ul>
          </article>
        </section>

        {/* ── Chart section ────────────────────────────────── */}
        <section className={styles.chartSection}>
          <div className={styles.chartCard}>
            <div className={styles.chartCardTop}>
              <div>
                <div className={styles.chartEyebrow}>Fiyat Hareketi · {period.toUpperCase()}</div>
                {periodDelta && (
                  <div className={styles.chartSubtitle}>
                    Son dönemde{' '}
                    <span style={{ color: chartPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                      {periodDelta} {chartPositive ? 'yükseliş' : 'düşüş'}
                    </span>
                  </div>
                )}
              </div>
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
            </div>

            <div className={styles.chartArea}>
              {chartError ? (
                <div className={styles.chartEmpty} style={{ color: 'var(--accent-red)' }}>{chartError}</div>
              ) : allPrices.length > 0 ? (
                <LineChart prices={allPrices} color={chartColor} height={280} />
              ) : (
                <div className={styles.chartEmpty}>Grafik verisi yükleniyor...</div>
              )}
            </div>

            <div className={styles.chartStats}>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>Dönem Yüksek</span>
                <span className={styles.chartStatValue}>
                  {high52 != null ? `₺${formatPrice(high52)}` : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>Dönem Düşük</span>
                <span className={styles.chartStatValue}>
                  {low52 != null ? `₺${formatPrice(low52)}` : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>F/K</span>
                <span className={styles.chartStatValue}>
                  {formatScoreNumber(fundamentals?.pe_ratio)}
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

        {/* ── Technical and fundamental dossiers ───────────── */}
        <section className={styles.dossierSection}>
          <article className={styles.dossierCard}>
            <div className={styles.cardHeaderLine}>
              <div>
                <div className={styles.sectionEyebrow}>Teknik Analiz</div>
                <h2>Trend, momentum, destek ve stop</h2>
              </div>
              <span className={styles.scoreChip}>{Number.isFinite(technical?.score) ? `${formatScoreNumber(technical?.score, 0)}/100` : '—'}</span>
            </div>
            <div className={styles.indicatorGrid}>
              {technicalRows.map((row) => (
                <div key={row.label} className={styles.indicatorRow}>
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                  <small>{row.note}</small>
                </div>
              ))}
            </div>
            <div className={styles.signalRows}>
              {(technical?.signals ?? []).slice(0, 8).map((signal, index) => (
                <div key={`${signal.type}-${index}`} className={styles.signalRow}>
                  <span>{signal.name}</span>
                  <strong data-direction={signal.direction}>{signal.direction === 'bullish' ? 'Pozitif' : signal.direction === 'bearish' ? 'Negatif' : 'Nötr'}</strong>
                  <small>{Number.isFinite(signal.strength) ? Math.round(signal.strength * 100) : 0} güç</small>
                </div>
              ))}
              {!technical?.signals?.length && <p className={styles.inlineEmpty}>Teknik sinyal oluşmadı.</p>}
            </div>
          </article>

          <article className={styles.dossierCard}>
            <div className={styles.cardHeaderLine}>
              <div>
                <div className={styles.sectionEyebrow}>Temel Analiz</div>
                <h2>Değerleme, kârlılık ve bilanço</h2>
              </div>
              <span className={styles.scoreChip}>{Number.isFinite(fundamentals?.fundamental_score) ? `${formatScoreNumber(fundamentals?.fundamental_score, 0)}/100` : '—'}</span>
            </div>
            <div className={styles.fundamentalRows}>
              {fundamentalRows.map((row) => (
                <div key={row.label} className={styles.fundamentalRow}>
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                  <small>{row.note}</small>
                </div>
              ))}
            </div>
            <div className={styles.watchBox}>
              <span>Takip edilecekler</span>
              <p>{watchRows.join(' · ')}</p>
            </div>
          </article>
        </section>

        {/* ── News dossier ─────────────────────────────────── */}
        <section className={styles.newsDossier}>
          <div className={styles.cardHeaderLine}>
            <div>
              <div className={styles.sectionEyebrow}>Haber ve KAP Takibi</div>
              <h2>Bu hisse hakkında gelen akış</h2>
            </div>
            <span className={styles.scoreChip}>{news.length} kayıt</span>
          </div>
          <div className={styles.stockNewsList}>
            {news.map((item) => (
              <NewsRow key={item.id} item={item} />
            ))}
            {!news.length && <p className={styles.inlineEmpty}>Bu hisseye bağlı haber kaydı yok.</p>}
          </div>
        </section>

        {/* ── Model rationale section ───────────────────── */}
        {scoreReasonRows.length > 0 && (
          <section className={styles.analysisSection}>
            <div className={styles.analysisCard}>
              <div className={styles.analysisEyebrow} style={{ color: 'var(--accent)' }}>
                ◆ Model Gerekçeleri
              </div>
              <div className={styles.analysisList}>
                {scoreReasonRows.map((component, index) => (
                  <div key={`${component.key}-${index}`} className={styles.analysisItem}>
                    <div className={styles.analysisItemTitle}>
                      {component.label} · {formatScoreNumber(component.raw_score)}
                    </div>
                    <div className={styles.analysisItemBody}>{component.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {peers.length > 0 && (
          <section className={styles.bottomSection}>
            <div className={styles.peersCard}>
              <div className={styles.fundCardHeader}>
                <div className={styles.fundEyebrow}>◆ Benzer Hisseler</div>
                <div className={styles.fundCardTitle}>{s.sector || 'Sektör'} sektöründen</div>
              </div>
              <div className={styles.peersTableWrap}>
                <div className={styles.peersTableHeader}>
                  <span>Hisse</span>
                  <span className={styles.peersRight}>Fiyat</span>
                  <span className={styles.peersRight}>Skor</span>
                  <span className={styles.peersRight}>%</span>
                </div>
                {peers.map((peer, index) => (
                  <Link key={`${peer.symbol}-${index}`} href={`/stocks/${peer.symbol}`} className={styles.peerRow}>
                    <div className={styles.peerSymbolWrap}>
                      <span className={styles.peerSymbol}>{peer.symbol}</span>
                      {peer.name && <span className={styles.peerName}>{peer.name}</span>}
                    </div>
                    <span className={styles.peerCell}>
                      {peer.current_price != null ? `₺${formatPrice(peer.current_price)}` : '—'}
                    </span>
                    <span className={styles.peerCell}>
                      {formatScoreNumber(peer.overall_score)}
                    </span>
                    <span
                      className={styles.peerCell}
                      style={{
                        color:
                          peer.daily_change_pct != null
                            ? peer.daily_change_pct >= 0
                              ? 'var(--accent-green)'
                              : 'var(--accent-red)'
                            : undefined,
                      }}
                    >
                      {peer.daily_change_pct != null
                        ? formatSignedPct(peer.daily_change_pct)
                        : '—'}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

      </div>
    </AppShell>
  );
}
