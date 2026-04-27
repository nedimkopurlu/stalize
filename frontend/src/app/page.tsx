'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import ScoreRing from '@/components/ScoreRing';
import RecommendationBadge, { PriceChange, formatPrice, formatVolume, formatMarketCap } from '@/components/StockHelpers';
import { TerminalEmpty, TerminalPageHeader, TerminalShell } from '@/components/TerminalPrimitives';
import api, {
  DashboardData,
  ModelPortfolioCurrentResponse,
  PortfolioHistoryResponse,
  PortfolioPosition,
  StockSummary,
  KapNotification,
  SparklineResponse,
} from '@/lib/api';
import type { MacroIndicators } from '@/lib/api';
import MacroPanel from '@/components/MacroPanel';
import SparklineWidget from '@/components/SparklineWidget';
import styles from './page.module.css';
import Link from 'next/link';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [allStocks, setAllStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [macroIndicators, setMacroIndicators] = useState<MacroIndicators | null>(null);
  const [macroLoading, setMacroLoading] = useState(true);
  const [modelPortfolio, setModelPortfolio] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [portfolioPositions, setPortfolioPositions] = useState<PortfolioPosition[]>([]);
  const [portfolioHistory, setPortfolioHistory] = useState<PortfolioHistoryResponse | null>(null);
  // KAP feed
  const [kapFeed, setKapFeed] = useState<KapNotification[]>([]);
  const [kapLoading, setKapLoading] = useState(true);
  // Sparkline data
  const [bist100Sparkline, setBist100Sparkline] = useState<SparklineResponse | null>(null);
  const [usdTrySparkline, setUsdTrySparkline] = useState<SparklineResponse | null>(null);
  const [sparklineLoading, setSparklineLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);

    // Macro indicators — non-blocking
    setMacroLoading(true);
    api.getMacroIndicators()
      .then(setMacroIndicators)
      .catch(() => setMacroIndicators(null))
      .finally(() => setMacroLoading(false));

    // KAP feed — non-blocking
    setKapLoading(true);
    api.getKapFeed(10)
      .then(setKapFeed)
      .catch(() => setKapFeed([]))
      .finally(() => setKapLoading(false));

    // Sparkline data — non-blocking
    setSparklineLoading(true);
    Promise.allSettled([
      api.getSparklineData('XU100', 30),
      api.getSparklineData('USDTRY=X', 30),
    ]).then(([bist, usd]) => {
      if (bist.status === 'fulfilled') setBist100Sparkline(bist.value);
      if (usd.status === 'fulfilled') setUsdTrySparkline(usd.value);
    }).finally(() => setSparklineLoading(false));

    try {
      const [
        dashboardResult,
        stocksResult,
        modelPortfolioResult,
        portfolioPositionsResult,
        portfolioHistoryResult,
      ] = await Promise.allSettled([
        api.getDashboard(),
        api.getStocks({ sort_by: 'overall_score', limit: 100 }),
        api.getCurrentModelPortfolio(),
        api.getPortfolioPositions(),
        api.getPortfolioHistory(30),
      ]);

      if (dashboardResult.status === 'fulfilled') {
        setData(dashboardResult.value);
      } else {
        setError(dashboardResult.reason instanceof Error ? dashboardResult.reason.message : 'Dashboard yüklenemedi');
      }

      if (stocksResult.status === 'fulfilled') {
        setAllStocks(stocksResult.value.stocks);
      }
      if (modelPortfolioResult.status === 'fulfilled') {
        setModelPortfolio(modelPortfolioResult.value);
      } else {
        setModelPortfolio(null);
      }
      if (portfolioPositionsResult.status === 'fulfilled') {
        setPortfolioPositions(portfolioPositionsResult.value);
      } else {
        setPortfolioPositions([]);
      }
      if (portfolioHistoryResult.status === 'fulfilled') {
        setPortfolioHistory(portfolioHistoryResult.value);
      } else {
        setPortfolioHistory(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'API bağlantı hatası');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner} />
          <p>Veriler yükleniyor...</p>
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>⚠️</div>
          <h2>Bağlantı Hatası</h2>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={loadData}>
            Tekrar Dene
          </button>
        </div>
      </AppShell>
    );
  }

  if (!data) return null;

  const modelWeek = modelPortfolio?.week ?? null;
  const modelHoldings = modelPortfolio?.holdings ?? [];
  const modelDecisionBand = modelPortfolio?.decision_band ?? null;
  const personalCurrentValue = portfolioPositions.reduce((sum, pos) => sum + (pos.current_price ?? pos.entry_price) * pos.quantity, 0);
  const personalInvestedValue = portfolioPositions.reduce((sum, pos) => sum + pos.entry_price * pos.quantity, 0);
  const personalReturnPct = personalInvestedValue > 0 ? ((personalCurrentValue - personalInvestedValue) / personalInvestedValue) * 100 : null;
  const personalBenchmarkSpread = portfolioHistory?.comparison.active_return_spread ?? null;

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Dashboard"
          description="BIST100 genel görünümü, model portföy, kişisel portföy ve öne çıkan akışları tek karar masasında topla."
          action={<button className="btn btn-primary" onClick={loadData}>Verileri Yenile</button>}
        />

        {/* ── 1. Makro Bant (üst, yatay) ─────────────────── */}
        <MacroPanel indicators={macroIndicators} loading={macroLoading} />

        {/* ── Stats Cards ───────────────────────────────── */}
        <div className={styles.statsGrid}>
          <StatCard label="Toplam Hisse" value={data.stats.total_stocks} icon="100" accent="cyan" />
          <StatCard label="Ort. Skor" value={data.stats.avg_score?.toFixed(1) ?? '—'} icon="AVG" accent="blue" />
          <StatCard label="AL Sinyali" value={data.stats.strong_buy_count + data.stats.buy_count} icon="AL" accent="green" />
          <StatCard label="SAT Sinyali" value={data.stats.sell_count + data.stats.strong_sell_count} icon="SAT" accent="red" />
          <StatCard label="TUT" value={data.stats.hold_count} icon="TUT" accent="amber" />
        </div>

        {/* ── 2. Ana İçerik + Sağ Sütun (KAP) ─────────── */}
        <div className={styles.mainLayout}>

          {/* Ana alan (~70%) */}
          <div className={styles.mainContent}>

            {/* 2a. Sparkline widget'ları */}
            <div className={styles.sparklineGrid}>
              {sparklineLoading ? (
                <>
                  <div className="glass-card skeleton" style={{ height: 96 }} />
                  <div className="glass-card skeleton" style={{ height: 96 }} />
                </>
              ) : (
                <>
                  <SparklineWidget
                    label="BIST100 — 30 Gün"
                    points={bist100Sparkline?.points ?? []}
                    height={60}
                  />
                  <SparklineWidget
                    label="USD/TRY — 30 Gün"
                    points={usdTrySparkline?.points ?? []}
                    height={60}
                  />
                </>
              )}
            </div>

            {/* 2b. Portföy kartları */}
            <div className={styles.portfolioGrid}>
              <div className={`card ${styles.portfolioCard}`}>
                <div className={styles.portfolioCardHeader}>
                  <div>
                    <h2 className={styles.sectionTitle}>Bu Haftaki Model Portföy</h2>
                    <p className={styles.intelligenceSub}>Sistemin otomatik kurduğu haftalık sepet</p>
                  </div>
                  <Link href="/model-portfolio" className="btn btn-ghost btn-sm">Ayrıntı →</Link>
                </div>
                <div className={styles.portfolioTopline}>
                  <PortfolioSignal
                    label="Haftalık Getiri"
                    value={formatSignedPercent(modelWeek?.portfolio_return_pct)}
                    tone={(modelWeek?.portfolio_return_pct ?? 0) >= 0 ? 'green' : 'red'}
                  />
                  <PortfolioSignal
                    label="BIST100 Farkı"
                    value={formatSignedPercent(modelWeek?.active_return_spread)}
                    tone={(modelWeek?.active_return_spread ?? 0) >= 0 ? 'green' : 'red'}
                  />
                  <PortfolioSignal
                    label="Pozisyon"
                    value={String(modelPortfolio?.summary?.holding_count ?? 0)}
                    tone="neutral"
                  />
                </div>
                {modelDecisionBand ? (
                  <div className={styles.decisionCard}>
                    <strong className={styles.decisionTitle}>{modelDecisionBand.headline}</strong>
                    <p className={styles.decisionFocus}>{modelDecisionBand.focus}</p>
                    {modelDecisionBand.actions.length ? (
                      <div className={styles.decisionList}>
                        {modelDecisionBand.actions.map((item) => (
                          <span key={item} className={styles.decisionItem}>{item}</span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {modelHoldings.length > 0 ? (
                  <div className={styles.portfolioRows}>
                    {modelHoldings.slice(0, 4).map((holding) => (
                      <div key={holding.id} className={styles.portfolioRow}>
                        <div>
                          <strong>{holding.symbol}</strong>
                          <span>{holding.sector || 'Sektör yok'}</span>
                        </div>
                        <div className={styles.portfolioRowRight}>
                          <span>%{holding.allocation_pct.toFixed(1)}</span>
                          <span className={(holding.daily_change_pct ?? 0) >= 0 ? styles.positive : styles.negative}>
                            {formatSignedPercent(holding.daily_change_pct)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <TerminalEmpty>Henüz model portföy üretilmedi.</TerminalEmpty>
                )}
              </div>

              <div className={`card ${styles.portfolioCard}`}>
                <div className={styles.portfolioCardHeader}>
                  <div>
                    <h2 className={styles.sectionTitle}>Portföyüm</h2>
                    <p className={styles.intelligenceSub}>Manuel yönettiğin kişisel portföy</p>
                  </div>
                  <Link href="/portfolio" className="btn btn-ghost btn-sm">Yönet →</Link>
                </div>
                <div className={styles.portfolioTopline}>
                  <PortfolioSignal label="Pozisyon" value={String(portfolioPositions.length)} tone="neutral" />
                  <PortfolioSignal
                    label="Getiri"
                    value={formatSignedPercent(personalReturnPct)}
                    tone={(personalReturnPct ?? 0) >= 0 ? 'green' : 'red'}
                  />
                  <PortfolioSignal
                    label="BIST100 Farkı"
                    value={formatSignedPercent(personalBenchmarkSpread)}
                    tone={(personalBenchmarkSpread ?? 0) >= 0 ? 'green' : 'red'}
                  />
                </div>
                {portfolioPositions.length > 0 ? (
                  <div className={styles.portfolioRows}>
                    {portfolioPositions.slice(0, 4).map((position) => (
                      <div key={position.id} className={styles.portfolioRow}>
                        <div>
                          <strong>{position.symbol}</strong>
                          <span>{position.rationale || 'Not girilmedi'}</span>
                        </div>
                        <div className={styles.portfolioRowRight}>
                          <span>{formatPrice(position.current_price)}</span>
                          <span className={(position.pnl_pct ?? 0) >= 0 ? styles.positive : styles.negative}>
                            {formatSignedPercent(position.pnl_pct)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <TerminalEmpty>Henüz kişisel portföyünde aktif pozisyon yok.</TerminalEmpty>
                )}
              </div>
            </div>

            {/* 2c. Top Buy & Sell */}
            <div className={styles.dualGrid}>
              <TopStocksCard title="Güçlü AL Sinyalleri" subtitle="En yüksek skorlu hisseler" stocks={data.top_buy} variant="buy" />
              <TopStocksCard title="SAT Sinyalleri" subtitle="En düşük skorlu hisseler" stocks={data.top_sell} variant="sell" />
            </div>

            {/* 2d. Hisse Skor Tablosu — glassmorphism .glass-card */}
            <div className={`glass-card ${styles.tableCard}`} style={{ padding: 0, overflow: 'hidden' }}>
              <div className={styles.tableHeader} style={{ padding: '20px 24px 16px' }}>
                <h2 className={styles.sectionTitle}>Tüm BIST100 Hisseleri</h2>
                <Link href="/stocks" className="btn btn-ghost btn-sm">Tümünü Gör →</Link>
              </div>
              <div className={styles.tableWrapper}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Hisse</th>
                      <th>Fiyat</th>
                      <th>Değişim</th>
                      <th className="hide-mobile">Hacim</th>
                      <th className="hide-mobile">P. Değeri</th>
                      <th>Teknik</th>
                      <th className="hide-mobile">Haber</th>
                      <th>Genel</th>
                      <th>Sinyal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allStocks.slice(0, 30).map((stock, i) => (
                      <tr key={stock.symbol} className="animate-fade-in" style={{ animationDelay: `${i * 20}ms` }}>
                        <td>
                          <Link href={`/stocks/${stock.symbol}`} className={styles.stockCell}>
                            <span className={styles.stockSymbol}>{stock.symbol}</span>
                            <span className={styles.stockName}>{stock.name?.substring(0, 30)}</span>
                          </Link>
                        </td>
                        <td className="font-mono">{formatPrice(stock.current_price)}</td>
                        <td><PriceChange value={stock.daily_change_pct} /></td>
                        <td className="hide-mobile text-muted font-mono">{formatVolume(stock.volume)}</td>
                        <td className="hide-mobile text-muted">{formatMarketCap(stock.market_cap)}</td>
                        <td><ScoreRing score={stock.technical_score} size={36} strokeWidth={3} /></td>
                        <td className="hide-mobile"><ScoreRing score={stock.sentiment_score} size={36} strokeWidth={3} /></td>
                        <td><ScoreRing score={stock.overall_score} size={40} strokeWidth={4} /></td>
                        <td><RecommendationBadge recommendation={stock.recommendation} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* ── 3. Sağ Sütun — KAP Bildirimleri ───────── */}
          <div className={styles.rightColumn}>
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '20px 20px 12px', borderBottom: '1px solid var(--glass-border)' }}>
                <h2 className={styles.sectionTitle}>KAP Bildirimleri</h2>
                <p className={styles.intelligenceSub}>Son 10 şirket açıklaması</p>
              </div>
              <div style={{ maxHeight: 500, overflowY: 'auto', padding: '8px 0' }}>
                {kapLoading ? (
                  <div style={{ padding: 16 }}>
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="skeleton" style={{ height: 56, borderRadius: 8, marginBottom: 8 }} />
                    ))}
                  </div>
                ) : kapFeed.length === 0 ? (
                  <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Henüz bildirim yok
                  </div>
                ) : (
                  kapFeed.map((item) => (
                    <KapFeedItem key={item.id} item={item} />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </TerminalShell>
    </AppShell>
  );
}

// ── KAP Feed Item ────────────────────────────────────────────

function KapFeedItem({ item }: { item: KapNotification }) {
  const dateStr = item.published_at
    ? new Date(item.published_at).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: '2-digit' })
    : '';

  const inner = (
    <div
      style={{
        padding: '10px 20px',
        borderBottom: '1px solid var(--glass-border)',
        transition: 'background 150ms ease',
        cursor: item.kap_url ? 'pointer' : 'default',
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)'; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
        {item.symbol ? (
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
            {item.symbol}
          </span>
        ) : (
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>KAP</span>
        )}
        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{dateStr}</span>
      </div>
      <div
        style={{
          fontSize: '0.78rem',
          color: 'var(--text-secondary)',
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          lineHeight: 1.4,
        }}
      >
        {item.title}
      </div>
    </div>
  );

  if (item.kap_url) {
    return (
      <a href={item.kap_url} target="_blank" rel="noopener noreferrer" style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}>
        {inner}
      </a>
    );
  }
  return inner;
}

// ── Sub Components ──────────────────────────────────────────

function StatCard({ label, value, icon, accent }: { label: string; value: string | number; icon: string; accent: string }) {
  const borderMap: Record<string, string> = {
    cyan: 'rgba(34, 211, 238, 0.2)', blue: 'rgba(59, 130, 246, 0.2)',
    green: 'rgba(34, 197, 94, 0.2)', red: 'rgba(239, 68, 68, 0.2)', amber: 'rgba(245, 158, 11, 0.2)',
  };
  const glowMap: Record<string, string> = {
    cyan: 'rgba(34, 211, 238, 0.06)', blue: 'rgba(59, 130, 246, 0.06)',
    green: 'rgba(34, 197, 94, 0.06)', red: 'rgba(239, 68, 68, 0.06)', amber: 'rgba(245, 158, 11, 0.06)',
  };
  return (
    <div className={`card ${styles.statCard}`} style={{ borderColor: borderMap[accent], background: glowMap[accent] }}>
      <div className={styles.statIcon}>{icon}</div>
      <div className={styles.statValue}>{value}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  );
}

function PortfolioSignal({ label, value, tone }: { label: string; value: string; tone: 'green' | 'red' | 'neutral' }) {
  return (
    <div className={`${styles.portfolioSignal} ${tone === 'green' ? styles.portfolioSignalGreen : tone === 'red' ? styles.portfolioSignalRed : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TopStocksCard({ title, subtitle, stocks, variant }: {
  title: string; subtitle: string; stocks: StockSummary[]; variant: 'buy' | 'sell';
}) {
  const borderColor = variant === 'buy' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)';
  return (
    <div className="card" style={{ borderColor }}>
      <div style={{ marginBottom: 16 }}>
        <h3 className={styles.sectionTitle}>{title}</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{subtitle}</p>
      </div>
      <div className={styles.topList}>
        {stocks.map((stock, i) => (
          <Link href={`/stocks/${stock.symbol}`} key={stock.symbol} className={styles.topItem}>
            <span className={styles.topRank}>#{i + 1}</span>
            <div className={styles.topInfo}>
              <span className={styles.topSymbol}>{stock.symbol}</span>
              <span className={styles.topName}>{stock.name?.substring(0, 25)}</span>
            </div>
            <div className={styles.topRight}>
              <ScoreRing score={stock.overall_score} size={36} strokeWidth={3} />
            </div>
          </Link>
        ))}
        {stocks.length === 0 && <TerminalEmpty>Henüz veri yok</TerminalEmpty>}
      </div>
    </div>
  );
}

function formatSignedPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '-';
  return `%${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}
