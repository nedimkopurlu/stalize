'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { formatPrice, formatVolume } from '@/components/StockHelpers';
import BistComparisonChart from '@/components/BistComparisonChart';
import api, { PortfolioHistoryResponse, PortfolioPosition, PortfolioRiskResponse, StockSummary } from '@/lib/api';
import styles from './page.module.css';

const PERIOD_OPTIONS = ['1H', '1A', '3A', '6A', '1Y', 'TÜMÜ'] as const;
type Period = typeof PERIOD_OPTIONS[number];
type WatchFilter = 'all' | 'up' | 'down' | 'volume';

const WATCH_FILTERS: { key: WatchFilter; label: string }[] = [
  { key: 'all', label: 'Tümü' },
  { key: 'up', label: 'Yükselen' },
  { key: 'down', label: 'Düşen' },
  { key: 'volume', label: 'Hacim' },
];

type PositionForm = {
  symbol: string;
  entry_price: string;
  quantity: string;
  entry_date: string;
  stop_loss: string;
  target_price: string;
  rationale: string;
};

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

const EMPTY_FORM: PositionForm = {
  symbol: '',
  entry_price: '',
  quantity: '',
  entry_date: todayISO(),
  stop_loss: '',
  target_price: '',
  rationale: '',
};

// ─── Risk thresholds (Phase 46 RISK-02, RISK-03) ───
const SECTOR_CONCENTRATION_THRESHOLD = 35;   // RISK-02: %35
const POSITION_CONCENTRATION_THRESHOLD = 20; // RISK-03: %20

// ─── Helpers ───

function formatTRY(value: number | null | undefined): string {
  if (value == null || isNaN(value) || !isFinite(value)) return '—';
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value: number | null | undefined, sign = true): string {
  if (value == null || isNaN(value) || !isFinite(value)) return '—';
  const prefix = sign && value > 0 ? '+' : '';
  return `${prefix}${value.toFixed(2)}%`;
}

function pnlClass(value: number | null | undefined): string {
  if (value == null) return styles.pnlNeutral;
  if (value > 0) return styles.pnlPositive;
  if (value < 0) return styles.pnlNegative;
  return styles.pnlNeutral;
}

function dayChangeClass(value: number | null | undefined): string {
  if (value == null) return styles.dayChangeNeutral;
  return value >= 0 ? styles.dayChangePositive : styles.dayChangeNegative;
}

function applyWatchFilter(stocks: StockSummary[], filter: WatchFilter): StockSummary[] {
  if (filter === 'up') return stocks.filter((stock) => (stock.daily_change_pct ?? 0) > 0);
  if (filter === 'down') return stocks.filter((stock) => (stock.daily_change_pct ?? 0) < 0);
  if (filter === 'volume') return [...stocks].sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0));
  return stocks;
}

// ─── SVG Portfolio Performance Chart ───

function PortfolioChart({
  series,
  period,
}: {
  series: Array<{ date: string; return_pct: number | null }>;
  period: Period;
}) {
  const filtered = useMemo(() => {
    if (!series.length) return series;
    const now = new Date();
    const cutoff = new Date(now);
    if (period === '1H') cutoff.setDate(now.getDate() - 7);
    else if (period === '1A') cutoff.setMonth(now.getMonth() - 1);
    else if (period === '3A') cutoff.setMonth(now.getMonth() - 3);
    else if (period === '6A') cutoff.setMonth(now.getMonth() - 6);
    else if (period === '1Y') cutoff.setFullYear(now.getFullYear() - 1);
    else return series; // TÜMÜ
    return series.filter((p) => new Date(p.date) >= cutoff);
  }, [series, period]);

  if (!filtered.length) {
    return (
      <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: 13 }}>
        Grafik için yeterli veri yok
      </div>
    );
  }

  const values = filtered.map((p) => p.return_pct ?? 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const W = 480;
  const H = 120;
  const PAD = 8;

  const points = values
    .map((v, i) => {
      const x = PAD + (i / Math.max(values.length - 1, 1)) * (W - PAD * 2);
      const y = H - PAD - ((v - min) / range) * (H - PAD * 2);
      return `${x},${y}`;
    })
    .join(' ');

  const last = values[values.length - 1];
  const isPositive = last >= 0;
  const lineColor = isPositive ? 'var(--accent-green)' : 'var(--accent-red)';

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height: 120, display: 'block' }}
    >
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.2" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* Zero line */}
      {min < 0 && max > 0 && (
        <line
          x1={PAD}
          x2={W - PAD}
          y1={H - PAD - ((0 - min) / range) * (H - PAD * 2)}
          y2={H - PAD - ((0 - min) / range) * (H - PAD * 2)}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="1"
          strokeDasharray="4 4"
        />
      )}
      {/* Fill area */}
      <polygon
        points={`${PAD},${H - PAD} ${points} ${W - PAD},${H - PAD}`}
        fill="url(#chartGrad)"
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ─── Recent Transactions ───

function RecentTransactions({ positions }: { positions: PortfolioPosition[] }) {
  if (!positions.length) {
    return <div className={styles.transEmpty}>İşlem geçmişi bulunamadı</div>;
  }

  const sorted = [...positions].sort(
    (a, b) => new Date(b.entry_date).getTime() - new Date(a.entry_date).getTime(),
  );

  return (
    <div className={styles.transList}>
      {sorted.slice(0, 8).map((pos, index) => {
        const value = (pos.current_price ?? pos.entry_price) * pos.quantity;
        const pnl = pos.pnl_pct;
        return (
          <div key={`${pos.id}-${pos.symbol}-${index}`} className={styles.transItem}>
            <div className={styles.transLeft}>
              <div className={styles.transDot}>📈</div>
              <div className={styles.transInfo}>
                <span className={styles.transSymbol}>{pos.symbol}</span>
                <span className={styles.transDate}>
                  {new Date(pos.entry_date).toLocaleDateString('tr-TR', {
                    day: '2-digit', month: 'short', year: 'numeric',
                  })}
                </span>
              </div>
            </div>
            <div className={styles.transRight}>
              <span className={styles.transValue}>{formatTRY(value)}</span>
              {pnl != null && (
                <span className={`${styles.transDelta} ${pnl >= 0 ? styles.transDeltaPos : styles.transDeltaNeg}`}>
                  {formatPct(pnl)}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main Page ───

export default function PortfolioPage() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [history, setHistory] = useState<PortfolioHistoryResponse | null>(null);
  const [watchStocks, setWatchStocks] = useState<StockSummary[]>([]);
  const [watchSymbols, setWatchSymbols] = useState<string[]>([]);
  const [loadingPositions, setLoadingPositions] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingWatchlist, setLoadingWatchlist] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [watchError, setWatchError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>('3A');
  const [watchFilter, setWatchFilter] = useState<WatchFilter>('all');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [form, setForm] = useState<PositionForm>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [riskGuard, setRiskGuard] = useState<PortfolioRiskResponse | null>(null);
  const [loadingRiskGuard, setLoadingRiskGuard] = useState(true);

  // PORT-02: position close state
  const [closingId, setClosingId] = useState<number | null>(null);
  const [closeForm, setCloseForm] = useState<{ exit_price: string; exit_date: string }>({
    exit_price: '',
    exit_date: todayISO(),
  });
  const [closeLoading, setCloseLoading] = useState(false);
  const [closeError, setCloseError] = useState<string | null>(null);

  useEffect(() => {
    void fetchPositions();
    void fetchHistory();
    void fetchWatchlist();
  }, []);

  useEffect(() => {
    if (loadingPositions) return;
    const active = positions.filter((p) => p.is_active !== false);
    const tv = active.reduce((s, p) => s + (p.current_price ?? p.entry_price) * p.quantity, 0);
    void fetchRiskGuard(tv);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positions, loadingPositions]);

  async function fetchPositions() {
    setLoadingPositions(true);
    try {
      const data = await api.getPortfolioPositions();
      setPositions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pozisyonlar alınamadı');
    } finally {
      setLoadingPositions(false);
    }
  }

  async function fetchHistory() {
    setLoadingHistory(true);
    try {
      const data = await api.getPortfolioHistory(365);
      setHistory(data);
    } catch {
      // History is non-blocking — silently skip
    } finally {
      setLoadingHistory(false);
    }
  }

  async function fetchRiskGuard(totalValue: number) {
    setLoadingRiskGuard(true);
    try {
      // Use 100000 fallback when portfolio is empty (mirrors api default)
      const safeValue = totalValue > 0 ? totalValue : 100000;
      const data = await api.getPortfolioRiskGuard(safeValue);
      setRiskGuard(data);
    } catch {
      // Non-blocking — silently skip (matches fetchHistory pattern)
      setRiskGuard(null);
    } finally {
      setLoadingRiskGuard(false);
    }
  }

  async function fetchWatchlist() {
    setLoadingWatchlist(true);
    setWatchError(null);
    try {
      const stored = JSON.parse(localStorage.getItem('stalize-watchlist') || '[]') as string[];
      const symbols = Array.from(new Set(stored.map((item) => item.trim().toUpperCase()).filter(Boolean)));
      setWatchSymbols(symbols);
      if (!symbols.length) {
        setWatchStocks([]);
        return;
      }
      const data = await api.getStocks({ symbols: symbols.join(','), limit: symbols.length });
      setWatchStocks(data.stocks);
    } catch (err) {
      setWatchError(err instanceof Error ? err.message : 'Takip listesi alınamadı');
      setWatchStocks([]);
    } finally {
      setLoadingWatchlist(false);
    }
  }

  function removeWatchSymbol(symbol: string) {
    const nextSymbols = watchSymbols.filter((item) => item !== symbol);
    localStorage.setItem('stalize-watchlist', JSON.stringify(nextSymbols));
    setWatchSymbols(nextSymbols);
    setWatchStocks((current) => current.filter((stock) => stock.symbol !== symbol));
  }

  function openAddForm() {
    setForm({ ...EMPTY_FORM, entry_date: todayISO() });
    setFormError(null);
    setIsAddOpen(true);
  }

  function closeAddForm() {
    if (isSubmitting) return;
    setIsAddOpen(false);
    setFormError(null);
  }

  function updateForm<K extends keyof PositionForm>(key: K, value: PositionForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submitPosition(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const symbol = form.symbol.trim().toUpperCase().replace(/\.IS$/, '');
    const entryPrice = Number(form.entry_price);
    const quantity = Number(form.quantity);
    const stopLoss = form.stop_loss.trim() ? Number(form.stop_loss) : undefined;
    const targetPrice = form.target_price.trim() ? Number(form.target_price) : undefined;

    if (!symbol) {
      setFormError('Sembol zorunlu.');
      return;
    }
    if (!Number.isFinite(entryPrice) || entryPrice <= 0) {
      setFormError('Alış fiyatı pozitif bir sayı olmalı.');
      return;
    }
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setFormError('Adet pozitif bir sayı olmalı.');
      return;
    }
    if (!form.entry_date) {
      setFormError('Alış tarihi zorunlu.');
      return;
    }
    if (stopLoss !== undefined && (!Number.isFinite(stopLoss) || stopLoss <= 0)) {
      setFormError('Stop seviyesi pozitif bir sayı olmalı.');
      return;
    }
    if (targetPrice !== undefined && (!Number.isFinite(targetPrice) || targetPrice <= 0)) {
      setFormError('Hedef fiyat pozitif bir sayı olmalı.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.addPosition({
        symbol,
        entry_price: entryPrice,
        quantity,
        entry_date: form.entry_date,
        ...(stopLoss !== undefined ? { stop_loss: stopLoss } : {}),
        ...(targetPrice !== undefined ? { target_price: targetPrice } : {}),
        ...(form.rationale.trim() ? { rationale: form.rationale.trim() } : {}),
      });
      setIsAddOpen(false);
      setForm({ ...EMPTY_FORM, entry_date: todayISO() });
      await Promise.all([fetchPositions(), fetchHistory()]);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Pozisyon eklenemedi.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // PORT-02: Split open vs closed positions
  const activePositions = positions.filter((p) => p.is_active !== false);
  const closedPositions = positions.filter((p) => p.is_active === false);

  // PORT-02: close position handler
  async function handleClosePosition() {
    if (closingId === null) return;
    const exitPrice = parseFloat(closeForm.exit_price);
    if (isNaN(exitPrice) || exitPrice <= 0) return;
    setCloseLoading(true);
    setCloseError(null);
    try {
      await api.closePosition(closingId, {
        exit_price: exitPrice,
        exit_date: closeForm.exit_date,
      });
      setClosingId(null);
      setCloseForm({ exit_price: '', exit_date: todayISO() });
      await Promise.all([fetchPositions(), fetchHistory()]);
    } catch (e) {
      setCloseError(e instanceof Error ? e.message : 'Pozisyon kapatılamadı.');
    } finally {
      setCloseLoading(false);
    }
  }

  // Derived values — only from active positions
  const investedValue = activePositions.reduce(
    (s, p) => s + p.entry_price * p.quantity, 0,
  );
  const currentValue = activePositions.reduce(
    (s, p) => s + (p.current_price ?? p.entry_price) * p.quantity, 0,
  );
  const totalPnl = currentValue - investedValue;
  const totalPnlPct = investedValue > 0 ? (totalPnl / investedValue) * 100 : null;

  // Day change from latest snapshot — only meaningful when there are active positions
  const latestSnapshot = history?.snapshots?.slice(-1)[0];
  const dayChangePct = activePositions.length > 0 ? (latestSnapshot?.daily_pnl_pct ?? null) : null;

  // Risk summary
  const risk = history?.risk_summary;
  const portfolioSeries = history?.comparison?.portfolio_series ?? [];
  const benchmarkSeries = history?.comparison?.benchmark_series ?? [];
  const benchmarkLabel = history?.comparison?.benchmark_label ?? 'BIST100';

  // Position weights — only active positions
  const positionsWithWeight = useMemo(() => {
    return activePositions.map((pos) => {
      const val = (pos.current_price ?? pos.entry_price) * pos.quantity;
      const weight = currentValue > 0 ? (val / currentValue) * 100 : 0;
      return { ...pos, weight, currentVal: val };
    });
  }, [activePositions, currentValue]);
  const displayedWatchStocks = useMemo(
    () => applyWatchFilter(watchStocks, watchFilter),
    [watchStocks, watchFilter],
  );

  // ─── Concentration alerts (RISK-02, RISK-03) ───
  type ConcentrationAlert = {
    key: string;
    kind: 'sector' | 'position';
    label: string;
    pct: number;
    threshold: number;
    message: string;
  };

  const concentrationAlerts = useMemo<ConcentrationAlert[]>(() => {
    if (!riskGuard) return [];
    const alerts: ConcentrationAlert[] = [];

    // Sector concentration (RISK-02)
    for (const sec of riskGuard.sector_exposure) {
      if (sec.exposure_pct > SECTOR_CONCENTRATION_THRESHOLD) {
        const name = sec.sector || 'Bilinmiyor';
        alerts.push({
          key: `sector-${sec.sector}`,
          kind: 'sector',
          label: name,
          pct: sec.exposure_pct,
          threshold: SECTOR_CONCENTRATION_THRESHOLD,
          message: `${name} sektöründe yoğunlaşma: %${sec.exposure_pct.toFixed(0)} ⚠ (eşik: %${SECTOR_CONCENTRATION_THRESHOLD})`,
        });
      }
    }

    // Single position concentration (RISK-03)
    for (const pos of riskGuard.positions) {
      if (pos.exposure_pct > POSITION_CONCENTRATION_THRESHOLD) {
        alerts.push({
          key: `position-${pos.symbol}`,
          kind: 'position',
          label: pos.symbol,
          pct: pos.exposure_pct,
          threshold: POSITION_CONCENTRATION_THRESHOLD,
          message: `${pos.symbol} tek hisse ağırlığı: %${pos.exposure_pct.toFixed(0)} ⚠ (eşik: %${POSITION_CONCENTRATION_THRESHOLD})`,
        });
      }
    }

    // Sort highest exposure first
    return alerts.sort((a, b) => b.pct - a.pct);
  }, [riskGuard]);

  // Risk level label
  function riskLabel(): string {
    if (!risk) return '--';
    if (risk.positions_at_risk === 0) return 'Düşük Risk';
    if (risk.positions_at_risk <= 1) return 'Orta Risk';
    return 'Yüksek Risk';
  }

  function riskDesc(): string {
    if (!risk) return 'Risk verisi hesaplanıyor…';
    return `${risk.active_positions} aktif pozisyon — ${risk.positions_at_risk} tanesi stop seviyesine yakın, ${risk.positions_near_target} tanesi hedefe yaklaşıyor.`;
  }

  return (
    <AppShell>
      <div className={styles.page}>

        {/* ─── Header ─── */}
        <div className={styles.header}>
          <p className={styles.eyebrow}>PORTFÖY MERKEZİ</p>
          <h1 className={styles.title}>Portföyüm ve takip listem</h1>
          <p className={styles.headerCopy}>
            Açık pozisyonlarını, risk özetini ve izlediğin hisseleri tek ekranda takip et.
          </p>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        {/* ─── Hero 2-col ─── */}
        <div className={styles.heroGrid}>

          {/* Left — Portfolio Value */}
          <div className={styles.card}>
            <p className={styles.cardEyebrow}>PORTFÖY DEĞERİM</p>

            {loadingPositions ? (
              <div className={styles.loadingWrap}>Yükleniyor…</div>
            ) : (
              <>
                <div className={styles.portfolioValue}>
                  {activePositions.length > 0 ? formatTRY(currentValue) : '--'}
                </div>

                <div className={`${styles.dayChange} ${dayChangeClass(dayChangePct)}`}>
                  {dayChangePct != null
                    ? `Bugün ${formatPct(dayChangePct)}`
                    : activePositions.length > 0 ? 'Günlük değişim hesaplanıyor' : 'Pozisyon eklenmedi'}
                </div>

                {activePositions.length > 0 && (
                  <div className={styles.totalPnl}>
                    Toplam K/Z:&nbsp;
                    <span className={`${styles.totalPnlValue} ${totalPnl >= 0 ? styles.totalPnlPos : styles.totalPnlNeg}`}>
                      {formatTRY(totalPnl)} ({formatPct(totalPnlPct)})
                    </span>
                  </div>
                )}

                {/* Period selector */}
                <div className={styles.periodTabs}>
                  {PERIOD_OPTIONS.map((p) => (
                    <button
                      key={p}
                      className={`${styles.periodTab} ${period === p ? styles.periodTabActive : ''}`}
                      onClick={() => setPeriod(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>

                {/* SVG Chart */}
                <div className={styles.chartWrap}>
                  {loadingHistory ? (
                    <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: 13 }}>
                      Grafik yükleniyor…
                    </div>
                  ) : (
                    <PortfolioChart series={portfolioSeries} period={period} />
                  )}
                </div>
              </>
            )}
          </div>

          {/* Right — AI Risk */}
          <div className={styles.card}>
            <div className={styles.riskHeader}>
              <div className={styles.riskIcon}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" stroke="#0d0e10" strokeWidth="2" strokeLinejoin="round" />
                  <path d="M12 12v4" stroke="#0d0e10" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="12" cy="9" r="1" fill="#0d0e10" />
                </svg>
              </div>
              <span className={styles.riskIconLabel}>Risk Özeti</span>
            </div>

            <div className={styles.riskLevel}>{riskLabel()}</div>
            <div className={styles.riskDesc}>{riskDesc()}</div>

            <div className={styles.riskRows}>
              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Açık pozisyon</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {activePositions.length} hisse
                  </span>
                  <span className={styles.riskRowNote}>Portföydeki açık pozisyon sayısı</span>
                </div>
              </div>

              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Stop yakın</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {risk?.positions_at_risk ?? '--'}
                  </span>
                  <span className={styles.riskRowNote}>Stop seviyesine yakın pozisyon</span>
                </div>
              </div>

              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Hedef yakın</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {risk?.positions_near_target ?? '--'}
                  </span>
                  <span className={styles.riskRowNote}>Hedef fiyatına yaklaşan pozisyon</span>
                </div>
              </div>

              <div className={`${styles.riskRow} ${styles.riskRowSectors}`}>
                <span className={styles.riskRowLabel}>En büyük 3 sektör</span>
                <div className={styles.riskRowRight}>
                  {loadingRiskGuard ? (
                    <span className={styles.riskRowNote}>Hesaplanıyor…</span>
                  ) : !riskGuard || riskGuard.sector_exposure.length === 0 ? (
                    <span className={styles.riskRowNote}>Aktif pozisyon yok</span>
                  ) : (
                    <span className={styles.riskRowSectorList}>
                      {[...riskGuard.sector_exposure]
                        .sort((a, b) => b.exposure_pct - a.exposure_pct)
                        .slice(0, 3)
                        .map((s) => `${s.sector || 'Bilinmiyor'} %${s.exposure_pct.toFixed(0)}`)
                        .join(', ')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ─── Yoğunlaşma Uyarıları (RISK-02, RISK-03) ─── */}
        {concentrationAlerts.length > 0 && (
          <section className={styles.riskAlerts} aria-label="Yoğunlaşma uyarıları">
            <p className={styles.riskAlertsTitle}>Yoğunlaşma Uyarıları</p>
            <ul className={styles.riskAlertsList}>
              {concentrationAlerts.map((alert) => (
                <li key={alert.key} className={styles.riskAlertItem}>
                  <span className={styles.riskAlertIcon} aria-hidden="true">⚠</span>
                  <span className={styles.riskAlertMessage}>{alert.message}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* ─── Sektör Dağılımı (RISK-01) ─── */}
        <section className={styles.sectorDist}>
          <div className={styles.sectorDistHeader}>
            <p className={styles.cardEyebrow}>SEKTÖR DAĞILIMI</p>
            <h2 className={styles.sectorDistTitle}>Portföyün sektörlere göre dağılımı</h2>
          </div>
          {loadingRiskGuard ? (
            <div className={styles.loadingWrap}>Sektör dağılımı yükleniyor…</div>
          ) : !riskGuard || riskGuard.sector_exposure.length === 0 ? (
            <div className={styles.transEmpty}>Sektör dağılımı için aktif pozisyon gerekli</div>
          ) : (
            <div className={styles.sectorList}>
              {[...riskGuard.sector_exposure]
                .sort((a, b) => b.exposure_pct - a.exposure_pct)
                .map((sec, idx) => (
                  <div
                    key={sec.sector}
                    className={`${styles.sectorRow} ${idx < 3 ? styles.sectorRowTop : ''}`}
                  >
                    <span className={styles.sectorName}>{sec.sector || 'Bilinmiyor'}</span>
                    <div className={styles.sectorBar}>
                      <div
                        className={styles.sectorBarFill}
                        style={{ width: `${Math.min(sec.exposure_pct, 100)}%` }}
                      />
                    </div>
                    <span className={styles.sectorPct}>{sec.exposure_pct.toFixed(1)}%</span>
                  </div>
                ))}
            </div>
          )}
        </section>

        {/* ─── Takip Listesi ─── */}
        <section className={styles.watchSection}>
          <div className={styles.watchHeader}>
            <div>
              <p className={styles.cardEyebrow}>TAKİP LİSTEM</p>
              <h2 className={styles.watchTitle}>
                {loadingWatchlist ? 'Takip listesi yükleniyor' : `${displayedWatchStocks.length}/${watchSymbols.length} hisse`}
              </h2>
            </div>
            <div className={styles.filterGroup}>
              {WATCH_FILTERS.map(({ key, label }) => (
                <button
                  key={key}
                  type="button"
                  className={`${styles.filterPill} ${watchFilter === key ? styles.filterPillActive : ''}`}
                  onClick={() => setWatchFilter(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {watchError ? (
            <div className={styles.errorBanner}>{watchError}</div>
          ) : (
            <div className={styles.tableScroll}>
              <table className={`${styles.table} ${styles.watchTable}`}>
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th className={styles.hideMobile}>Şirket</th>
                    <th className={styles.hideMobile}>Sektör</th>
                    <th>Fiyat</th>
                    <th>Günlük</th>
                    <th>Skor</th>
                    <th className={styles.hideMobile}>Hacim</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingWatchlist ? (
                    Array.from({ length: 4 }).map((_, index) => (
                      <tr key={`watch-loading-${index}`}>
                        {Array.from({ length: 8 }).map((__, cellIndex) => (
                          <td key={cellIndex}>
                            <div className={styles.skeletonLine} />
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : displayedWatchStocks.length === 0 ? (
                    <tr>
                      <td colSpan={8}>
                        <div className={styles.emptyStateCompact}>
                          <strong>{watchSymbols.length === 0 ? 'Takip listen boş' : 'Bu filtrede hisse yok'}</strong>
                          <span>Hisse detayındaki “Takibe Al” düğmesiyle buraya ekleyebilirsin.</span>
                          <Link href="/stocks" className={styles.inlineLink}>Hisselere git</Link>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    displayedWatchStocks.map((stock) => {
                      const change = stock.daily_change_pct;
                      return (
                        <tr key={stock.symbol}>
                          <td>
                            <Link href={`/stocks/${stock.symbol}`} className={styles.symbolLink}>
                              {stock.symbol}
                            </Link>
                          </td>
                          <td className={styles.hideMobile} style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                            {stock.name ?? '—'}
                          </td>
                          <td className={styles.hideMobile} style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                            {stock.sector ?? '—'}
                          </td>
                          <td>{formatPrice(stock.current_price)}</td>
                          <td className={pnlClass(change)}>{formatPct(change)}</td>
                          <td>{stock.overall_score != null ? stock.overall_score.toFixed(1) : '—'}</td>
                          <td className={styles.hideMobile}>{formatVolume(stock.volume)}</td>
                          <td>
                            <button
                              type="button"
                              className={styles.removeWatchBtn}
                              onClick={() => removeWatchSymbol(stock.symbol)}
                            >
                              Çıkar
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ─── Pozisyonlarım Table ─── */}
        <div className={styles.positionsSection}>
          <div className={styles.positionsHeader}>
            <h2 className={styles.positionsTitle}>
              Pozisyonlarım
              <span className={styles.positionsCount}>{activePositions.length} hisse</span>
            </h2>
            <div className={styles.positionsActions}>
              <button className={styles.btnGhost} disabled>
                İhraç et
              </button>
              <button className={styles.btnAccent} onClick={openAddForm}>
                + Yeni Pozisyon
              </button>
            </div>
          </div>

          {loadingPositions ? (
            <div className={styles.loadingWrap}>Pozisyonlar yükleniyor…</div>
          ) : activePositions.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📊</div>
              <p className={styles.emptyTitle}>Henüz pozisyon eklenmedi</p>
              <p className={styles.emptyDesc}>
                Portföyünü takip etmek için hisse pozisyonlarınızı ekleyin.
                Alış fiyatı, adet ve tarih bilgisiyle K/Z takibini başlatın.
              </p>
              <button className={styles.emptyAction} onClick={openAddForm}>
                Pozisyon ekle
              </button>
            </div>
          ) : (
            <div className={styles.tableScroll}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th className={styles.hideMobile}>Şirket</th>
                    <th>Adet</th>
                    <th>Maliyet</th>
                    <th>Son</th>
                    <th>Değer</th>
                    <th>K/Z</th>
                    <th>K/Z%</th>
                    <th className={styles.hideMobile}>Ağırlık</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {positionsWithWeight.map((pos, index) => {
                    const cost = pos.entry_price * pos.quantity;
                    const pnlAbs = pos.currentVal - cost;
                    return (
                      <tr key={`${pos.id}-${pos.symbol}-${index}`}>
                        <td>
                          <Link
                            href={`/stocks/${pos.symbol}`}
                            style={{ textDecoration: 'none' }}
                          >
                            <div className={styles.symbolCell}>
                              <span className={styles.symbolName}>{pos.symbol}</span>
                              <span className={styles.symbolDate}>
                                {new Date(pos.entry_date).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })}
                              </span>
                            </div>
                          </Link>
                        </td>
                        <td className={styles.hideMobile} style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                          {pos.symbol}
                          {pos.partial && (
                            <span className={styles.partialMark} title="Kısmi fiyat verisi">~</span>
                          )}
                        </td>
                        <td>{pos.quantity.toLocaleString('tr-TR')}</td>
                        <td>{formatPrice(pos.entry_price)}</td>
                        <td>{formatPrice(pos.current_price)}</td>
                        <td>{formatTRY(pos.currentVal)}</td>
                        <td className={pnlClass(pnlAbs)}>
                          {isNaN(pnlAbs) ? '—' : `${pnlAbs >= 0 ? '+' : ''}${formatTRY(pnlAbs)}`}
                        </td>
                        <td className={pnlClass(pos.pnl_pct)}>
                          {formatPct(pos.pnl_pct)}
                        </td>
                        <td className={styles.hideMobile}>
                          <div className={styles.weightCell}>
                            <div className={styles.weightBar}>
                              <div
                                className={styles.weightBarFill}
                                style={{ width: `${Math.min(pos.weight, 100)}%` }}
                              />
                            </div>
                            <span className={styles.weightText}>
                              {pos.weight.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td>
                          {closingId === pos.id ? (
                            <div className={styles.closeForm}>
                              <input
                                type="number"
                                step="0.01"
                                min="0.01"
                                placeholder="Çıkış fiyatı"
                                value={closeForm.exit_price}
                                onChange={(e) => setCloseForm((f) => ({ ...f, exit_price: e.target.value }))}
                                className={styles.closeInput}
                              />
                              <input
                                type="date"
                                value={closeForm.exit_date}
                                onChange={(e) => setCloseForm((f) => ({ ...f, exit_date: e.target.value }))}
                                className={styles.closeInput}
                              />
                              <button
                                className={styles.closeConfirm}
                                onClick={handleClosePosition}
                                disabled={closeLoading}
                              >
                                {closeLoading ? '...' : 'Onayla'}
                              </button>
                              <button
                                className={styles.closeCancel}
                                onClick={() => { setClosingId(null); setCloseError(null); }}
                              >
                                İptal
                              </button>
                              {closeError && closingId === pos.id && (
                                <span style={{ color: 'var(--accent-red)', fontSize: 11 }}>{closeError}</span>
                              )}
                            </div>
                          ) : (
                            <button
                              className={styles.closeBtn}
                              onClick={() => {
                                setClosingId(pos.id);
                                setCloseForm((f) => ({
                                  ...f,
                                  exit_price: pos.current_price ? String(pos.current_price) : '',
                                }));
                              }}
                            >
                              Kapat
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ─── Geçmiş Pozisyonlar ─── */}
        {closedPositions.length > 0 && (
          <div className={styles.positionsSection}>
            <div className={styles.positionsHeader}>
              <h2 className={styles.positionsTitle}>
                Geçmiş Pozisyonlar
                <span className={styles.positionsCount}>{closedPositions.length} kapalı</span>
              </h2>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Son 30 gün</span>
            </div>
            <div className={styles.tableScroll}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th>Çıkış Tarihi</th>
                    <th>Alış</th>
                    <th>Satış</th>
                    <th>Adet</th>
                    <th>Gerçek K/Z (TL)</th>
                    <th>Gerçek K/Z%</th>
                  </tr>
                </thead>
                <tbody>
                  {closedPositions.map((pos, idx) => {
                    const realizedPct = pos.realized_pnl !== null && pos.entry_price > 0 && pos.exit_price !== null
                      ? ((pos.exit_price - pos.entry_price) / pos.entry_price) * 100
                      : null;
                    return (
                      <tr key={`closed-${pos.id}-${idx}`}>
                        <td><span className={styles.symbolName}>{pos.symbol}</span></td>
                        <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                          {pos.exit_date
                            ? new Date(pos.exit_date).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' })
                            : '—'}
                        </td>
                        <td>{formatPrice(pos.entry_price)}</td>
                        <td>{pos.exit_price != null ? formatPrice(pos.exit_price) : '—'}</td>
                        <td>{pos.quantity.toLocaleString('tr-TR')}</td>
                        <td className={pnlClass(pos.realized_pnl)}>
                          {pos.realized_pnl !== null
                            ? `${pos.realized_pnl >= 0 ? '+' : ''}${formatTRY(pos.realized_pnl)}`
                            : '—'}
                        </td>
                        <td className={pnlClass(realizedPct)}>
                          {formatPct(realizedPct)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ─── BIST100 Karşılaştırma Grafiği (PORT-04 / FEAT-03) ─── */}
        {(portfolioSeries.length > 0 || benchmarkSeries.length > 0) && (
          <BistComparisonChart
            portfolioSeries={portfolioSeries}
            benchmarkSeries={benchmarkSeries}
            benchmarkLabel={benchmarkLabel}
          />
        )}

        {/* ─── Bottom 2-col ─── */}
        <div className={styles.bottomGrid}>

          {/* Left — Pozisyon Ağırlıkları */}
          <div className={styles.sectorCard}>
            <h3 className={styles.sectionTitle}>Pozisyon Ağırlıkları</h3>
            {positionsWithWeight.length === 0 ? (
              <div className={styles.sectorEmpty}>Pozisyon bulunmuyor</div>
            ) : (
              <div className={styles.sectorLegend}>
                {positionsWithWeight
                  .sort((a, b) => b.weight - a.weight)
                  .map((pos, index) => (
                    <div key={`${pos.id}-${pos.symbol}-${index}`} className={styles.sectorLegendItem}>
                      <span className={styles.sectorLegendLabel}>{pos.symbol}</span>
                      <span className={styles.sectorLegendPct}>{pos.weight.toFixed(1)}%</span>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Right — Son İşlemler */}
          <div className={styles.transCard}>
            <h3 className={styles.sectionTitle}>Son İşlemler</h3>
            <RecentTransactions positions={activePositions} />
          </div>
        </div>

        {isAddOpen && (
          <div className={styles.modalBackdrop} role="presentation" onClick={closeAddForm}>
            <form className={styles.positionModal} onSubmit={submitPosition} onClick={(event) => event.stopPropagation()}>
              <div className={styles.modalHeader}>
                <div>
                  <p className={styles.modalEyebrow}>MANUEL POZİSYON</p>
                  <h3 className={styles.modalTitle}>Yeni Pozisyon</h3>
                </div>
                <button type="button" className={styles.modalClose} onClick={closeAddForm} aria-label="Kapat">
                  ×
                </button>
              </div>

              <div className={styles.formGrid}>
                <label className={styles.field}>
                  <span>Sembol</span>
                  <input
                    value={form.symbol}
                    onChange={(event) => updateForm('symbol', event.target.value.toUpperCase())}
                    placeholder="THYAO"
                    autoFocus
                  />
                </label>
                <label className={styles.field}>
                  <span>Alış tarihi</span>
                  <input
                    type="date"
                    value={form.entry_date}
                    onChange={(event) => updateForm('entry_date', event.target.value)}
                  />
                </label>
                <label className={styles.field}>
                  <span>Alış fiyatı</span>
                  <input
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    value={form.entry_price}
                    onChange={(event) => updateForm('entry_price', event.target.value)}
                    placeholder="312.50"
                  />
                </label>
                <label className={styles.field}>
                  <span>Adet</span>
                  <input
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.0001"
                    value={form.quantity}
                    onChange={(event) => updateForm('quantity', event.target.value)}
                    placeholder="10"
                  />
                </label>
                <label className={styles.field}>
                  <span>Stop seviyesi</span>
                  <input
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    value={form.stop_loss}
                    onChange={(event) => updateForm('stop_loss', event.target.value)}
                    placeholder="Opsiyonel"
                  />
                </label>
                <label className={styles.field}>
                  <span>Hedef fiyat</span>
                  <input
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    value={form.target_price}
                    onChange={(event) => updateForm('target_price', event.target.value)}
                    placeholder="Opsiyonel"
                  />
                </label>
              </div>

              <label className={styles.field}>
                <span>Not</span>
                <textarea
                  value={form.rationale}
                  onChange={(event) => updateForm('rationale', event.target.value)}
                  placeholder="Opsiyonel"
                  rows={3}
                />
              </label>

              {formError && <div className={styles.formError}>{formError}</div>}

              <div className={styles.modalActions}>
                <button type="button" className={styles.btnGhost} onClick={closeAddForm}>
                  Vazgeç
                </button>
                <button type="submit" className={styles.btnAccent} disabled={isSubmitting}>
                  {isSubmitting ? 'Ekleniyor…' : 'Pozisyon ekle'}
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </AppShell>
  );
}
