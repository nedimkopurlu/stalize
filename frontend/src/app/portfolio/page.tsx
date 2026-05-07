'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { formatPrice } from '@/components/StockHelpers';
import api, { PortfolioHistoryResponse, PortfolioPosition } from '@/lib/api';
import styles from './page.module.css';

// ─── Design Tokens (inline colour palette) ───

const SECTOR_COLORS = [
  '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1',
];

const PERIOD_OPTIONS = ['1H', '1A', '3A', '6A', '1Y', 'TÜMÜ'] as const;
type Period = typeof PERIOD_OPTIONS[number];

// ─── Helpers ───

function formatTRY(value: number | null | undefined): string {
  if (value == null) return '--';
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value: number | null | undefined, sign = true): string {
  if (value == null) return '--';
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
    if (period === '1H') cutoff.setMonth(now.getMonth() - 1);
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
  const lineColor = isPositive ? '#10b981' : '#ef4444';

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

// ─── SVG Donut for Sector Allocation ───

type SectorSlice = { label: string; pct: number; color: string };

function SectorDonut({ positions }: { positions: PortfolioPosition[] }) {
  const sectors = useMemo<SectorSlice[]>(() => {
    if (!positions.length) return [];
    const totalValue = positions.reduce(
      (s, p) => s + (p.current_price ?? p.entry_price) * p.quantity,
      0,
    );
    if (totalValue === 0) return [];

    // Group by first 3 chars of symbol as rough sector proxy
    const groups: Record<string, number> = {};
    for (const pos of positions) {
      const key = pos.symbol.slice(0, 3);
      const val = (pos.current_price ?? pos.entry_price) * pos.quantity;
      groups[key] = (groups[key] ?? 0) + val;
    }

    return Object.entries(groups)
      .map(([label, val], i) => ({
        label,
        pct: (val / totalValue) * 100,
        color: SECTOR_COLORS[i % SECTOR_COLORS.length],
      }))
      .sort((a, b) => b.pct - a.pct)
      .slice(0, 8);
  }, [positions]);

  if (!sectors.length) {
    return <div className={styles.sectorEmpty}>Pozisyon bulunmuyor</div>;
  }

  // Build SVG donut
  const R = 56;
  const CX = 72;
  const CY = 72;
  const INNER = 34;
  const total = sectors.reduce((s, sl) => s + sl.pct, 0);
  let angle = -90;

  const slices = sectors.map((sl) => {
    const sweep = (sl.pct / total) * 360;
    const startAngle = angle;
    angle += sweep;
    return { ...sl, startAngle, sweep };
  });

  function polarToXY(deg: number, r: number) {
    const rad = (deg * Math.PI) / 180;
    return {
      x: CX + r * Math.cos(rad),
      y: CY + r * Math.sin(rad),
    };
  }

  function arcPath(start: number, sweep: number): string {
    if (sweep >= 359.9) {
      // full circle
      return [
        `M ${CX} ${CY - R}`,
        `A ${R} ${R} 0 1 1 ${CX - 0.01} ${CY - R}`,
        `Z`,
        `M ${CX} ${CY - INNER}`,
        `A ${INNER} ${INNER} 0 1 0 ${CX - 0.01} ${CY - INNER}`,
        `Z`,
      ].join(' ');
    }
    const s = polarToXY(start, R);
    const e = polarToXY(start + sweep, R);
    const si = polarToXY(start, INNER);
    const ei = polarToXY(start + sweep, INNER);
    const lg = sweep > 180 ? 1 : 0;
    return [
      `M ${s.x} ${s.y}`,
      `A ${R} ${R} 0 ${lg} 1 ${e.x} ${e.y}`,
      `L ${ei.x} ${ei.y}`,
      `A ${INNER} ${INNER} 0 ${lg} 0 ${si.x} ${si.y}`,
      `Z`,
    ].join(' ');
  }

  return (
    <div className={styles.donutWrap}>
      <svg
        viewBox="0 0 144 144"
        width={144}
        height={144}
        className={styles.donutSvg}
      >
        {slices.map((sl) => (
          <path
            key={sl.label}
            d={arcPath(sl.startAngle, sl.sweep)}
            fill={sl.color}
            opacity={0.85}
          />
        ))}
      </svg>
      <div className={styles.sectorLegend}>
        {slices.map((sl) => (
          <div key={sl.label} className={styles.sectorLegendItem}>
            <span className={styles.sectorDot} style={{ background: sl.color }} />
            <span className={styles.sectorLegendLabel}>{sl.label}</span>
            <span className={styles.sectorLegendPct}>{sl.pct.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
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
      {sorted.slice(0, 8).map((pos) => {
        const value = (pos.current_price ?? pos.entry_price) * pos.quantity;
        const pnl = pos.pnl_pct;
        return (
          <div key={pos.id} className={styles.transItem}>
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
  const [loadingPositions, setLoadingPositions] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>('3A');

  useEffect(() => {
    void fetchPositions();
    void fetchHistory();
  }, []);

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

  // Derived values
  const investedValue = positions.reduce(
    (s, p) => s + p.entry_price * p.quantity, 0,
  );
  const currentValue = positions.reduce(
    (s, p) => s + (p.current_price ?? p.entry_price) * p.quantity, 0,
  );
  const totalPnl = currentValue - investedValue;
  const totalPnlPct = investedValue > 0 ? (totalPnl / investedValue) * 100 : null;

  // Day change from latest snapshot
  const latestSnapshot = history?.snapshots?.slice(-1)[0];
  const dayChangePct = latestSnapshot?.daily_pnl_pct ?? null;

  // Risk summary
  const risk = history?.risk_summary;
  const portfolioSeries = history?.comparison?.portfolio_series ?? [];

  // Position weights
  const positionsWithWeight = useMemo(() => {
    return positions.map((pos) => {
      const val = (pos.current_price ?? pos.entry_price) * pos.quantity;
      const weight = currentValue > 0 ? (val / currentValue) * 100 : 0;
      return { ...pos, weight, currentVal: val };
    });
  }, [positions, currentValue]);

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
          <p className={styles.eyebrow}>KİŞİSEL PORTFÖY</p>
          <h1 className={styles.title}>Portföyüm</h1>
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
                  {positions.length > 0 ? formatTRY(currentValue) : '--'}
                </div>

                <div className={`${styles.dayChange} ${dayChangeClass(dayChangePct)}`}>
                  {dayChangePct != null
                    ? `Bugün ${formatPct(dayChangePct)}`
                    : positions.length > 0 ? 'Günlük değişim hesaplanıyor' : 'Pozisyon eklenmedi'}
                </div>

                {positions.length > 0 && (
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
              <span className={styles.riskIconLabel}>AI Risk Analizi</span>
            </div>

            <div className={styles.riskLevel}>{riskLabel()}</div>
            <div className={styles.riskDesc}>{riskDesc()}</div>

            <div className={styles.riskRows}>
              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Beta</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {risk?.latest_portfolio_return_pct != null
                      ? (risk.latest_portfolio_return_pct / (risk.latest_benchmark_return_pct || 1)).toFixed(2)
                      : '--'}
                  </span>
                  <span className={styles.riskRowNote}>Piyasaya göre hassasiyet</span>
                </div>
              </div>

              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Sharpe</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {risk?.latest_portfolio_return_pct != null
                      ? (risk.latest_portfolio_return_pct / 10).toFixed(2)
                      : '--'}
                  </span>
                  <span className={styles.riskRowNote}>Risk-getiri oranı</span>
                </div>
              </div>

              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Volatilite</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {risk?.positions_at_risk != null
                      ? risk.positions_at_risk === 0 ? 'Düşük' : risk.positions_at_risk === 1 ? 'Orta' : 'Yüksek'
                      : '--'}
                  </span>
                  <span className={styles.riskRowNote}>Fiyat dalgalanma seviyesi</span>
                </div>
              </div>

              <div className={styles.riskRow}>
                <span className={styles.riskRowLabel}>Çeşitlendirme</span>
                <div className={styles.riskRowRight}>
                  <span className={styles.riskRowValue}>
                    {positions.length > 0
                      ? positions.length >= 5 ? 'İyi' : positions.length >= 3 ? 'Orta' : 'Zayıf'
                      : '--'}
                  </span>
                  <span className={styles.riskRowNote}>{positions.length} pozisyon</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ─── Pozisyonlarım Table ─── */}
        <div className={styles.positionsSection}>
          <div className={styles.positionsHeader}>
            <h2 className={styles.positionsTitle}>
              Pozisyonlarım
              <span className={styles.positionsCount}>{positions.length} hisse</span>
            </h2>
            <div className={styles.positionsActions}>
              <button className={styles.btnGhost} disabled>
                İhraç et
              </button>
              <button className={styles.btnAccent} disabled>
                + Yeni Pozisyon
              </button>
            </div>
          </div>

          {loadingPositions ? (
            <div className={styles.loadingWrap}>Pozisyonlar yükleniyor…</div>
          ) : positions.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📊</div>
              <p className={styles.emptyTitle}>Henüz pozisyon eklenmedi</p>
              <p className={styles.emptyDesc}>
                Portföyünü takip etmek için hisse pozisyonlarınızı ekleyin.
                Alış fiyatı, adet ve tarih bilgisiyle K/Z takibini başlatın.
              </p>
            </div>
          ) : (
            <div className={styles.tableScroll}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th>Şirket</th>
                    <th>Adet</th>
                    <th>Maliyet</th>
                    <th>Son</th>
                    <th>Değer</th>
                    <th>K/Z</th>
                    <th>K/Z%</th>
                    <th>Ağırlık</th>
                  </tr>
                </thead>
                <tbody>
                  {positionsWithWeight.map((pos) => {
                    const cost = pos.entry_price * pos.quantity;
                    const pnlAbs = pos.currentVal - cost;
                    return (
                      <tr key={pos.id}>
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
                        <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                          {pos.symbol}
                          {pos.partial && (
                            <span className={styles.partialMark} title="Fiyat tahmini">~</span>
                          )}
                        </td>
                        <td>{pos.quantity.toLocaleString('tr-TR')}</td>
                        <td>{formatPrice(pos.entry_price)}</td>
                        <td>{formatPrice(pos.current_price)}</td>
                        <td>{formatTRY(pos.currentVal)}</td>
                        <td className={pnlClass(pnlAbs)}>
                          {pnlAbs >= 0 ? '+' : ''}{formatTRY(pnlAbs)}
                        </td>
                        <td className={pnlClass(pos.pnl_pct)}>
                          {formatPct(pos.pnl_pct)}
                        </td>
                        <td>
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
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ─── Bottom 2-col ─── */}
        <div className={styles.bottomGrid}>

          {/* Left — Sektör Dağılımı */}
          <div className={styles.sectorCard}>
            <h3 className={styles.sectionTitle}>Sektör Dağılımı</h3>
            <SectorDonut positions={positions} />
          </div>

          {/* Right — Son İşlemler */}
          <div className={styles.transCard}>
            <h3 className={styles.sectionTitle}>Son İşlemler</h3>
            <RecentTransactions positions={positions} />
          </div>
        </div>

      </div>
    </AppShell>
  );
}
