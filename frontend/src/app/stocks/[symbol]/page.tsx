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

// ── Bull / Bear thesis generator ─────────────────────────────

interface Thesis {
  title: string;
  body: string;
}

function getBullTheses(sector: string | null, symbol: string, recommendation: string | null): Thesis[] {
  const isBuy = recommendation === 'AL' || recommendation === 'GÜÇLÜ AL';
  const sectorTheses: Record<string, Thesis[]> = {
    'Savunma': [
      { title: 'Artan savunma bütçeleri', body: 'NATO üyesi ülkelerin savunma harcamalarını artırması, ihracat gelirlerini doğrudan besliyor.' },
      { title: 'Yerli üretim avantajı', body: 'İthal ikamesi politikaları kapsamında yerli savunma şirketlerine öncelikli ihaleler veriliyor.' },
      { title: 'Teknoloji katma değeri', body: 'Yüksek teknolojili ürün portföyü, marj baskısını kısmen sınırlıyor ve fiyatlandırma gücü sağlıyor.' },
    ],
    'Havacılık': [
      { title: 'Sezonsal talep artışı', body: 'Yaz sezonu öncesinde trafik verileri güçlü seyrediyor; kapasite kullanımı kritik eşiğin üzerinde.' },
      { title: 'Yakıt fiyatı desteği', body: 'Jet yakıtı fiyatlarındaki gerileme, operasyonel maliyetleri olumlu etkiliyor.' },
      { title: 'Rota çeşitlendirmesi', body: 'Yeni açılan rotalar ve ortak uçuş anlaşmaları, yolcu başına geliri artırıyor.' },
    ],
    'Bankacılık': [
      { title: 'Faiz marjı genişlemesi', body: 'TCMB\'nin faiz indirim döngüsü, bankaların net faiz marjını olumlu yönde etkileyecek.' },
      { title: 'Kredi büyümesi ivmeleniyor', body: 'Ekonomik canlanmayla birlikte bireysel ve ticari kredi talebi hız kazanıyor.' },
      { title: 'Sermaye yeterliliği güçlü', body: 'SYR oranı sektör ortalamasının üzerinde seyrediyor; olası şoklara karşı tampon sağlıyor.' },
    ],
    'Teknoloji': [
      { title: 'Dijitalleşme rüzgârı', body: 'Kurumsal dijital dönüşüm yatırımları artmaya devam ediyor; talep yapısal olarak güçlü.' },
      { title: 'Yüksek marjlı iş modeli', body: 'Yazılım ve lisans gelirleri, hizmet segmentine kıyasla belirgin biçimde daha yüksek marj sunuyor.' },
      { title: 'İhracat büyümesi', body: 'Döviz geliri sağlayan ihracat portföyü, kur volatilitesine karşı doğal bir koruma işlevi görüyor.' },
    ],
  };

  const defaultTheses: Thesis[] = [
    { title: isBuy ? 'Güçlü AI sinyali' : 'Değerleme avantajı', body: isBuy ? 'AI modelimiz çoklu faktör analiziyle bu hisseyi pozitif olarak değerlendiriyor.' : 'Mevcut fiyat seviyeleri, uzun vadeli yatırımcılar için cazip bir giriş noktası sunuyor.' },
    { title: 'Sektör liderliği', body: `${sector || 'Sektör'} içinde öne çıkan konumuyla rakiplere karşı sürdürülebilir rekabet avantajı sağlıyor.` },
    { title: 'Temettü potansiyeli', body: 'Güçlü serbest nakit akışı, sürdürülebilir ve büyüyen temettü ödemelerini destekliyor.' },
  ];

  return sectorTheses[sector ?? ''] ?? defaultTheses;
}

function getBearTheses(sector: string | null, symbol: string): Thesis[] {
  const sectorBears: Record<string, Thesis[]> = {
    'Savunma': [
      { title: 'Proje gecikme riski', body: 'Büyük ölçekli savunma projelerinde yaşanan gecikmeler, gelir tanıma zamanlamasını olumsuz etkileyebilir.' },
      { title: 'Döviz kuru maruziyeti', body: 'USD/TRY volatilitesi, maliyet yapısını ve ithalat girdilerini olumsuz etkileyebilir.' },
      { title: 'Konsantrasyon riski', body: 'Gelirin büyük bölümünün az sayıda müşteriden gelmesi, müşteri kaybı riskini artırıyor.' },
    ],
    'Bankacılık': [
      { title: 'Takipteki kredi artışı', body: 'Ekonomik yavaşlama senaryosunda sorunlu kredi oranlarında artış yaşanabilir.' },
      { title: 'Regülasyon baskısı', body: 'BDDK düzenlemeleri ve kredi büyüme sınırlamaları, karlılığı kısıtlayabilir.' },
      { title: 'Enflasyon belirsizliği', body: 'Yüksek enflasyon ortamı, reel kredi büyümesini ve mevduat maliyetlerini olumsuz etkileyebilir.' },
    ],
  };

  const defaultBears: Thesis[] = [
    { title: 'Makro volatilite', body: 'Yüksek faiz ortamı ve döviz kuru dalgalanmaları, değerleme çarpanlarına baskı yapabilir.' },
    { title: 'Rekabet yoğunlaşması', body: 'Sektöre yeni girişler ve uluslararası rekabet, pazar payını ve fiyatlandırma gücünü tehdit edebilir.' },
    { title: 'Likidite riski', body: 'Küresel risk iştahındaki ani daralma, yabancı yatırımcı çıkışıyla birlikte keskin satış baskısı getirebilir.' },
  ];

  return sectorBears[sector ?? ''] ?? defaultBears;
}

// ── Deterministic insider mock data ─────────────────────────

interface InsiderMove {
  initials: string;
  name: string;
  role: string;
  date: string;
  action: 'AL' | 'SAT';
  amount: string;
}

function getInsiderMoves(symbol: string): InsiderMove[] {
  const seed = symbol.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const names = [
    { name: 'Ahmet Kaya', role: 'Yönetim Kurulu Başkanı', initials: 'AK' },
    { name: 'Fatma Demir', role: 'CFO', initials: 'FD' },
    { name: 'Mehmet Yılmaz', role: 'CEO', initials: 'MY' },
    { name: 'Zeynep Arslan', role: 'Bağımsız Üye', initials: 'ZA' },
    { name: 'Hakan Çelik', role: 'Genel Müdür', initials: 'HÇ' },
  ];
  const amounts = ['₺2.4M', '₺850K', '₺4.1M', '₺1.2M', '₺680K'];
  const dates = ['8 May 2025', '2 May 2025', '25 Nis 2025', '18 Nis 2025', '10 Nis 2025'];

  return names.map((n, i) => ({
    ...n,
    date: dates[i],
    action: (seed + i) % 3 === 0 ? 'SAT' : 'AL',
    amount: amounts[(seed + i) % amounts.length],
  }));
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

function getHeroTagline(sector: string | null, rec: string | null): { kicker: string; title: string } {
  const isBuy = rec === 'AL' || rec === 'GÜÇLÜ AL';
  const isSell = rec === 'SAT' || rec === 'GÜÇLÜ SAT';

  if (isBuy) {
    const sectorLines: Record<string, { kicker: string; title: string }> = {
      'Savunma': { kicker: 'Savunma harcamaları rüzgârı', title: 'kanatlarına' },
      'Havacılık': { kicker: 'Sezonsal momentum başlıyor', title: 'yüksekten uçuyor' },
      'Bankacılık': { kicker: 'Faiz indirim döngüsü', title: 'marjları açıyor' },
      'Teknoloji': { kicker: 'Dijital dönüşüm ivmesi', title: 'öne çıkıyor' },
    };
    return sectorLines[sector ?? ''] ?? { kicker: `${sector ?? 'Sektör'} momentumu`, title: 'öne çıkıyor' };
  }

  if (isSell) {
    return { kicker: 'Risk faktörleri gündemde', title: 'değerlemesi baskı altında' };
  }

  return { kicker: `${sector ?? 'Sektör'} gelişmeleri`, title: 'odakta' };
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
  const changeArrow = chartPositive ? '▲' : '▼';

  const PERIODS = [
    { key: '1d', label: '1G' },
    { key: '1wk', label: '1H' },
    { key: '1m', label: '1A' },
    { key: '3m', label: '3A' },
    { key: '6m', label: '6A' },
    { key: '1y', label: '1Y' },
    { key: '5y', label: '5Y' },
  ];

  const tagline = getHeroTagline(s.sector, recommendation);
  const bullTheses = getBullTheses(s.sector, s.symbol, recommendation);
  const bearTheses = getBearTheses(s.sector, s.symbol);
  const insiderMoves = getInsiderMoves(s.symbol);
  const periodDelta = getPeriodDelta(allPrices);

  // target price & upside potential
  const targetPrice = technical?.target_price ?? s.target_price ?? null;
  const stopLoss = technical?.stop_loss ?? s.stop_loss ?? null;
  const upsidePct = (() => {
    if (targetPrice && s.current_price && s.current_price > 0) {
      const pct = ((targetPrice - s.current_price) / s.current_price) * 100;
      return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
    }
    return null;
  })();

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
            <Link href="#" className={styles.tradeBtn} onClick={(e) => e.preventDefault()}>
              Al / Sat
            </Link>
          </div>
        </div>

        {/* ── Hero section ──────────────────────────────────── */}
        <section className={styles.hero}>
          {/* Left column */}
          <div className={styles.heroLeft}>
            <p className={styles.eyebrow}>
              {s.symbol} · {s.name} · {s.is_bist30 ? 'BIST 30' : 'BIST 100'}
            </p>

            <h1 className={styles.heroTitle}>
              <span className={styles.heroTitleLine}>{tagline.kicker},</span>
              <br />
              <em className={styles.heroSymbolItalic}>{s.symbol}</em>
              {' '}<span>{tagline.title}</span>
            </h1>

            <p className={styles.heroDesc}>
              {s.sector ? `${s.sector} sektöründe faaliyet gösteren` : ''} {s.name},{' '}
              BIST&apos;te işlem gören önemli hisseler arasında yer almaktadır.{' '}
              {aiConfidence != null && recommendation ? (
                <>
                  AI modelimiz bu hisseyi{' '}
                  <span className={styles.confidenceBadge}>
                    %{aiConfidence} güvenle {recommendation}
                  </span>{' '}
                  olarak işaretliyor.
                </>
              ) : null}
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
                    {changeArrow} {s.daily_change_pct >= 0 ? '+' : ''}{s.daily_change_pct.toFixed(2)}%
                  </span>
                  <span className={styles.heroPriceChangeDate}>Bugün · itibarıyla</span>
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
                <span className={styles.scoreCardTitle}>AI Skor Kartı</span>
              </div>

              <div className={styles.scoreCardSignal}>
                <div>
                  <div className={styles.signalLabelSmall}>Sinyal</div>
                  <div
                    className={styles.signalLabel}
                    style={{ color: recColor(recommendation) }}
                  >
                    {recommendation ?? 'VERİ YOK'}
                  </div>
                </div>
                {s.overall_score != null && (
                  <span className={styles.signalScore}>{s.overall_score.toFixed(1)}</span>
                )}
              </div>

              {s.overall_score != null && (
                <div className={styles.signalConfidence}>
                  %{Math.round(s.overall_score)} güven
                </div>
              )}

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
                    {targetPrice != null ? `₺${formatPrice(targetPrice)}` : '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Yukarı potansiyel</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-green)' }}>
                    {upsidePct ?? '—'}
                  </span>
                </div>
                <div className={styles.scoreCardRow}>
                  <span className={styles.scoreCardRowLabel}>Stop-loss önerisi</span>
                  <span className={styles.scoreCardRowValue} style={{ color: 'var(--accent-red)' }}>
                    {stopLoss != null ? `₺${formatPrice(stopLoss)}` : '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
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
              {allPrices.length > 0 ? (
                <LineChart prices={allPrices} color={chartColor} height={280} />
              ) : (
                <div className={styles.chartEmpty}>Grafik verisi yükleniyor...</div>
              )}
            </div>

            <div className={styles.chartStats}>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>52H Yüksek</span>
                <span className={styles.chartStatValue}>
                  {high52 != null ? `₺${formatPrice(high52)}` : '—'}
                </span>
              </div>
              <div className={styles.chartStat}>
                <span className={styles.chartStatLabel}>52H Düşük</span>
                <span className={styles.chartStatValue}>
                  {low52 != null ? `₺${formatPrice(low52)}` : '—'}
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

        {/* ── 3-column analysis section ───────────────────── */}
        <section className={styles.analysisSection}>
          {/* Bull Theses */}
          <div className={styles.analysisCard}>
            <div className={styles.analysisEyebrow} style={{ color: 'var(--accent-green)' }}>
              ▲ Boğa Tezleri
            </div>
            <div className={styles.analysisList}>
              {bullTheses.map((thesis, i) => (
                <div key={i} className={styles.analysisItem}>
                  <div className={styles.analysisItemTitle}>{thesis.title}</div>
                  <div className={styles.analysisItemBody}>{thesis.body}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Bear Theses */}
          <div className={styles.analysisCard}>
            <div className={styles.analysisEyebrow} style={{ color: 'var(--accent-red)' }}>
              ▼ Ayı Tezleri
            </div>
            <div className={styles.analysisList}>
              {bearTheses.map((thesis, i) => (
                <div key={i} className={styles.analysisItem}>
                  <div className={styles.analysisItemTitle}>{thesis.title}</div>
                  <div className={styles.analysisItemBody}>{thesis.body}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Insider Moves */}
          <div className={styles.analysisCard}>
            <div className={styles.analysisEyebrow} style={{ color: 'var(--accent)' }}>
              ◆ İçeriden Hareketler
            </div>
            <div className={styles.insiderList}>
              {insiderMoves.map((move, i) => (
                <div key={i} className={styles.insiderRow}>
                  <div className={styles.insiderAvatar}>{move.initials}</div>
                  <div className={styles.insiderInfo}>
                    <div className={styles.insiderName}>{move.name}</div>
                    <div className={styles.insiderMeta}>{move.role} · {move.date}</div>
                  </div>
                  <div className={styles.insiderRight}>
                    <span
                      className={styles.insiderBadge}
                      style={{
                        background: move.action === 'AL' ? 'rgba(16,185,129,.15)' : 'rgba(239,68,68,.15)',
                        color: move.action === 'AL' ? 'var(--accent-green)' : 'var(--accent-red)',
                      }}
                    >
                      {move.action}
                    </span>
                    <div className={styles.insiderAmount}>{move.amount}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Temel Analiz + Benzer Hisseler ───────────────── */}
        <section className={styles.bottomSection}>
          {/* Fundamentals */}
          <div className={styles.fundCard}>
            <div className={styles.fundCardHeader}>
              <div className={styles.fundEyebrow}>Temel Analiz</div>
              <div className={styles.fundCardTitle}>Anahtar oranlar</div>
            </div>
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
                <span className={styles.fundLabel}>EV/FAVÖK</span>
                <span className={styles.fundValue}>
                  {fundamentals?.ev_ebitda != null
                    ? fundamentals.ev_ebitda.toFixed(1)
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
          </div>

          {/* Peers */}
          {peers.length > 0 && (
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
                {peers.map((peer) => (
                  <Link key={peer.symbol} href={`/stocks/${peer.symbol}`} className={styles.peerRow}>
                    <div className={styles.peerSymbolWrap}>
                      <span className={styles.peerSymbol}>{peer.symbol}</span>
                      {peer.name && <span className={styles.peerName}>{peer.name}</span>}
                    </div>
                    <span className={styles.peerCell}>
                      {peer.current_price != null ? `₺${formatPrice(peer.current_price)}` : '—'}
                    </span>
                    <span className={styles.peerCell}>
                      {peer.overall_score != null ? peer.overall_score.toFixed(1) : '—'}
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
                        ? `${peer.daily_change_pct >= 0 ? '+' : ''}${peer.daily_change_pct.toFixed(2)}%`
                        : '—'}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </section>

      </div>
    </AppShell>
  );
}
