'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { PriceChange, formatPrice, formatVolume } from '@/components/StockHelpers';
import {
  api,
  Bist100HistoryResponse,
  DashboardData,
  IntelligenceOverview,
  MarketBist100Response,
  MarketForexResponse,
  MarketGoldResponse,
  StockSummary,
} from '@/lib/api';
import styles from './page.module.css';

const PERIODS = ['1A', '3A', '1Y'] as const;
type Period = (typeof PERIODS)[number];

const FOREX_TR_LABELS: Record<string, string> = {
  'USDTRY=X': 'Dolar',
  'EURTRY=X': 'Avro',
  'GBPTRY=X': 'Sterlin',
  'JPYTRY=X': 'Japon Yeni',
  'CHFTRY=X': 'İsviçre Frangı',
};

function pct(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

function asDate(value: string | null | undefined) {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' });
}

function shortText(text: string | null | undefined, length = 190) {
  if (!text) return '';
  return text.length > length ? `${text.slice(0, length).trim()}...` : text;
}

function MarketChart({ points, period, up }: { points: Bist100HistoryResponse['points']; period: Period; up: boolean }) {
  const values = useMemo(() => {
    const count = period === '1A' ? 30 : period === '3A' ? 90 : 252;
    return points.slice(-count).map((point) => point.close);
  }, [period, points]);

  if (values.length < 2) {
    return <div className={styles.chartEmpty}>Günlük kapanış verisi bekleniyor.</div>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 720;
  const height = 220;
  const line = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 12) - 6;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg className={styles.chart} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <polyline
        points={line}
        fill="none"
        stroke={up ? 'var(--accent-green)' : 'var(--accent-red)'}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
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

export default function DashboardPage() {
  const [bist, setBist] = useState<MarketBist100Response | null>(null);
  const [history, setHistory] = useState<Bist100HistoryResponse | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [intel, setIntel] = useState<IntelligenceOverview | null>(null);
  const [forex, setForex] = useState<MarketForexResponse | null>(null);
  const [gold, setGold] = useState<MarketGoldResponse | null>(null);
  const [dailySummary, setDailySummary] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>('1A');
  const [search, setSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<StockSummary[]>([]);

  const load = useCallback(() => {
    api.getMarketBist100().then(setBist).catch(() => null);
    api.getMarketBist100History(365).then(setHistory).catch(() => null);
    api.getDashboard().then(setDashboard).catch(() => null);
    api.getIntelligenceOverview(6).then(setIntel).catch(() => null);
    api.getMarketForex().then(setForex).catch(() => null);
    api.getMarketGold().then(setGold).catch(() => null);
    api.getDailySummary().then((value) => setDailySummary(value.summary)).catch(() => null);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(load, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => {
    if (search.trim().length < 2) {
      return;
    }
    const timer = window.setTimeout(() => {
      api
        .getStocks({ search: search.trim(), limit: 8 })
        .then((result) => setSearchResults(result.stocks))
        .catch(() => setSearchResults([]));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === 'Escape') setSearchOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const topIdeas = dashboard?.top_buy.slice(0, 4) ?? [];
  const marketTone = (bist?.daily_change_pct ?? 0) >= 0;
  const majorNews = intel?.feed.slice(0, 5) ?? [];
  const stats = dashboard?.stats;
  const marketMood = stats
    ? stats.buy_count + stats.strong_buy_count > stats.sell_count + stats.strong_sell_count
      ? 'Seçici pozitif'
      : 'Temkinli'
    : 'Veri bekleniyor';

  return (
    <AppShell>
      <main className={styles.page}>
        <section className={styles.topBar}>
          <button className={styles.searchButton} type="button" onClick={() => setSearchOpen(true)}>
            Hisse ara
            <kbd>⌘K</kbd>
          </button>
        </section>

        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <span className={styles.eyebrow}>Genel Borsa Özeti</span>
            <h1>BIST’te bugün genel resim</h1>
            <p>{shortText(dailySummary, 260) || 'Piyasa özeti hazırlanıyor.'}</p>
            <div className={styles.marketFacts}>
              <Fact label="Piyasa modu" value={marketMood} />
              <Fact label="Ortalama skor" value={stats?.avg_score != null ? stats.avg_score.toFixed(1) : '-'} />
              <Fact label="Al bölgesi" value={stats ? String(stats.buy_count + stats.strong_buy_count) : '-'} />
            </div>
          </div>

          <div className={styles.indexCard}>
            <div className={styles.indexHeader}>
              <div>
                <span className={styles.eyebrow}>BIST 100</span>
                <strong>{formatPrice(bist?.value ?? null)}</strong>
              </div>
              <PriceChange value={bist?.daily_change_pct ?? null} />
            </div>
            <div className={styles.periods}>
              {PERIODS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={period === item ? styles.activePeriod : ''}
                  onClick={() => setPeriod(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            <MarketChart points={history?.points ?? []} period={period} up={marketTone} />
            <div className={styles.indexMeta}>
              <span>Son veri: {asDate(bist?.as_of)}</span>
              <span>Hacim: {formatVolume(bist?.volume ?? null)}</span>
            </div>
          </div>
        </section>

        <section className={styles.ideaSection}>
          <div className={styles.sectionHeader}>
            <div>
              <span className={styles.eyebrow}>Bugünün Adayları</span>
              <h2>Neyi neden izlemeliyim?</h2>
            </div>
            <Link href="/stocks">Tüm hisseler</Link>
          </div>
          <div className={styles.ideaGrid}>
            {topIdeas.map((stock) => (
              <Link key={stock.symbol} href={`/stocks/${stock.symbol}`} className={styles.ideaCard}>
                <div className={styles.ideaTop}>
                  <strong>{stock.symbol}</strong>
                  <span title={safeLabelTooltip(stock.recommendation)}>
                    {safeLabel(stock.recommendation)}
                  </span>
                </div>
                <p>{stock.name}</p>
                <div className={styles.ideaScores}>
                  <span>Skor {Math.round(stock.overall_score ?? 0)}</span>
                  <span>Teknik {Math.round(stock.technical_score ?? 0)}</span>
                  <span>Temel {Math.round(stock.fundamental_score ?? 0)}</span>
                </div>
                <small>
                  {stock.sector} · {pct(stock.daily_change_pct)}
                </small>
              </Link>
            ))}
          </div>
        </section>

        <section className={styles.marketGrid}>
          <article className={styles.panel}>
            <div className={styles.panelHead}>
              <h2>Piyasa haberleri</h2>
              <Link href="/intelligence">Tümü</Link>
            </div>
            <div className={styles.newsList}>
              {majorNews.map((item) => (
                <a key={item.trigger_id} href={item.source_url ?? '#'} target="_blank" rel="noreferrer">
                  <span>{item.publisher ?? 'Kaynak'}{item.symbol ? ` · ${item.symbol}` : ''}</span>
                  <strong>{item.headline}</strong>
                </a>
              ))}
              {!majorNews.length && <p className={styles.empty}>Haber akışı bekleniyor.</p>}
            </div>
          </article>

          <article className={styles.panel}>
            <div className={styles.panelHead}>
              <h2>Döviz ve altın</h2>
            </div>
            <div className={styles.assetList}>
              {forex?.pairs.slice(0, 4).map((pair) => (
                <AssetRow key={pair.symbol} label={FOREX_TR_LABELS[pair.symbol] ?? pair.name} value={`₺${formatPrice(pair.rate)}`} change={pair.daily_change_pct} />
              ))}
              <AssetRow label="Gram Altın" value={`₺${formatPrice(gold?.forms.gram ?? null)}`} />
              <AssetRow label="Ons Altın" value={`$${formatPrice(gold?.gold_usd_per_oz ?? null)}`} />
            </div>
          </article>
        </section>

        {searchOpen && (
          <div className={styles.searchOverlay} role="dialog" aria-modal="true">
            <button className={styles.backdrop} type="button" aria-label="Aramayı kapat" onClick={() => setSearchOpen(false)} />
            <div className={styles.searchDialog}>
              <input
                autoFocus
                placeholder="THYAO, banka, enerji..."
                value={search}
                onChange={(event) => {
                  const value = event.target.value.toUpperCase();
                  setSearch(value);
                  if (value.trim().length < 2) setSearchResults([]);
                }}
              />
              <div className={styles.searchResults}>
                {search.trim().length < 2 && <p>Hisse veya sektör yaz.</p>}
                {search.trim().length >= 2 && !searchResults.length && <p>Sonuç yok.</p>}
                {searchResults.map((stock) => (
                  <Link key={stock.symbol} href={`/stocks/${stock.symbol}`} onClick={() => setSearchOpen(false)}>
                    <span>
                      <strong>{stock.symbol}</strong>
                      <small>{stock.name} · {stock.sector}</small>
                    </span>
                    <b>{formatPrice(stock.current_price)}</b>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </AppShell>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.fact}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function AssetRow({ label, value, change }: { label: string; value: string; change?: number | null }) {
  return (
    <div className={styles.assetRow}>
      <span>{label}</span>
      <strong>{value}</strong>
      {change !== undefined && <PriceChange value={change ?? null} />}
    </div>
  );
}
