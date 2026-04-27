'use client';

import React, { useCallback, useEffect, useState, use } from 'react';
import AppShell from '@/components/AppShell';
import { formatPrice, formatVolume, formatMarketCap } from '@/components/StockHelpers';
import api, { KapNewsItem, ScoreBreakdownResponse, StockDetail, StockFundamentals, StockPricesResponse, TechnicalResult } from '@/lib/api';
import CandlestickEMAPanel from '@/components/CandlestickEMAPanel';
import FundamentalMetricCard from '@/components/FundamentalMetricCard';
import KAPNewsCard from '@/components/KAPNewsCard';
import ScoreLayerPanel from '@/components/ScoreLayerPanel';
import { TerminalEmpty, TerminalPageHeader, TerminalShell } from '@/components/TerminalPrimitives';
import styles from './stock.module.css';
import Link from 'next/link';

export default function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = use(params);
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [prices, setPrices] = useState<StockPricesResponse | null>(null);
  const [technical, setTechnical] = useState<TechnicalResult | null>(null);
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdownResponse | null>(null);
  const [fundamentals, setFundamentals] = useState<StockFundamentals | null>(null);
  const [kapNews, setKapNews] = useState<KapNewsItem[]>([]);
  const [fundLoading, setFundLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [period, setPeriod] = useState('1y');
  const [loading, setLoading] = useState(true);

  const loadStock = useCallback(async () => {
    setLoading(true);
    try {
      const [det, tech] = await Promise.all([
        api.getStockDetail(symbol),
        api.getStockTechnical(symbol).catch(() => null),
      ]);
      setDetail(det);
      setTechnical(tech);
      const breakdown = await api.getStockScoreBreakdown(symbol).catch(() => null);
      setScoreBreakdown(breakdown);

      // Fundamentals and KAP news — parallel, non-blocking
      api.getStockFundamentals(symbol)
        .then(f => setFundamentals(f))
        .catch(() => setFundamentals(null))
        .finally(() => setFundLoading(false));

      api.getStockNews(symbol, 5)
        .then(r => setKapNews(r.items))
        .catch(() => setKapNews([]))
        .finally(() => setNewsLoading(false));
    } catch {
      /* API error */
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  const loadPrices = useCallback(async () => {
    try {
      const response = await api.getStockPrices(symbol, period);
      setPrices(response);
    } catch {
      /* */
    }
  }, [period, symbol]);

  useEffect(() => {
    void loadStock();
  }, [loadStock]);

  useEffect(() => {
    void loadPrices();
  }, [loadPrices]);

  if (loading) {
    return (
      <AppShell>
        <div className={styles.loadingState}>
          <div className={styles.spinner} />
        </div>
      </AppShell>
    );
  }

  if (!detail) {
    return (
      <AppShell>
        <TerminalEmpty>Hisse bulunamadı</TerminalEmpty>
      </AppShell>
    );
  }

  const s = detail.stock;

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title={`${s.symbol} Detay`}
          description={`${s.name || s.symbol} için fiyat, teknik yapı, skor dağılımı ve son haber akışını birlikte incele.`}
          action={(
            <button className="btn btn-primary" onClick={() => void loadStock()}>
              Veriyi Yenile
            </button>
          )}
        />

        {/* ── Breadcrumb ─────────────────────────────── */}
        <div className={styles.breadcrumb}>
          <Link href="/">Dashboard</Link>
          <span>/</span>
          <Link href="/stocks">Hisseler</Link>
          <span>/</span>
          <span className={styles.breadcrumbActive}>{s.symbol}</span>
        </div>

        {/* ── 3-Layer Score Panel ────────────────────── */}
        <ScoreLayerPanel stock={s} />

        {/* ── Score Breakdown ────────────────────────── */}
        {scoreBreakdown && (
          <section className={`card ${styles.breakdownCard}`}>
            <div className={styles.breakdownHeader}>
              <div>
                <h3 className={styles.sectionTitle}>Skor Breakdown</h3>
                <p className={styles.breakdownSubtext}>
                  Toplam skor {scoreBreakdown.breakdown.overall_score.toFixed(2)} · {scoreBreakdown.breakdown.recommendation}
                </p>
              </div>
              <div className={styles.breakdownCoverage}>
                Ağırlık Kapsaması {(scoreBreakdown.breakdown.summary.weight_coverage * 100).toFixed(0)}%
              </div>
            </div>

            <div className={styles.breakdownGrid}>
              {scoreBreakdown.breakdown.components.map((component) => (
                <div key={component.key} className={styles.breakdownItem}>
                  <div className={styles.breakdownTop}>
                    <span className={styles.breakdownLabel}>{component.label}</span>
                    <span className={styles.breakdownContribution}>+{component.contribution.toFixed(2)}</span>
                  </div>
                  <div className={styles.breakdownValues}>
                    <span>Skor {component.raw_score.toFixed(2)}</span>
                    <span>Ağırlık {(component.normalized_weight * 100).toFixed(0)}%</span>
                  </div>
                  <p className={styles.breakdownReason}>{component.reason}</p>
                </div>
              ))}
            </div>

            {scoreBreakdown.breakdown.missing_components.length > 0 && (
              <div className={styles.missingBox}>
                <div className={styles.missingTitle}>Eksik Katmanlar</div>
                <div className={styles.missingList}>
                  {scoreBreakdown.breakdown.missing_components.map((component) => (
                    <div key={component.key} className={styles.missingItem}>
                      <strong>{component.label}</strong>
                      <span>{component.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* ── Chart Section (full width) ─────────────── */}
        <div className={styles.glassCard} style={{ marginBottom: 20 }}>
          <div className={styles.chartHeader}>
            <h3 className={styles.sectionTitle}>Fiyat Grafiği</h3>
            <div className={styles.periodBar}>
              {['1m', '3m', '6m', '1y', '5y'].map(p => (
                <button
                  key={p}
                  className={`tab-item ${period === p ? 'active' : ''}`}
                  onClick={() => setPeriod(p)}
                >
                  {p.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <CandlestickEMAPanel
            prices={prices?.prices ?? []}
            ema50={technical?.ema_50 ?? []}
            ema200={technical?.ema_200 ?? []}
          />
        </div>

        {/* ── Metrics Row (2 columns, middle) ───────── */}
        <div className={styles.metricsRow} style={{ marginBottom: 20 }}>
          {/* Temel Metrikler */}
          <div className={styles.glassCard}>
            <FundamentalMetricCard fundamentals={fundamentals} loading={fundLoading} />
          </div>

          {/* Risk Seviyeleri */}
          <div className={styles.glassCard}>
            <h3 className={styles.sectionTitle}>Risk Seviyeleri</h3>
            {technical ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {technical.stop_loss != null && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Stop-Loss (2×ATR)</span>
                    <span style={{ color: 'var(--red-500)', fontFamily: 'monospace', fontWeight: 600 }}>
                      {technical.stop_loss.toFixed(2)} ₺
                    </span>
                  </div>
                )}
                {technical.target_price != null && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Hedef Fiyat</span>
                    <span style={{ color: 'var(--green-500)', fontFamily: 'monospace', fontWeight: 600 }}>
                      {technical.target_price.toFixed(2)} ₺
                    </span>
                  </div>
                )}
                {(technical.support != null || technical.resistance != null) && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                    {technical.support != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Destek</span>
                        <span style={{ color: 'var(--green-400)', fontFamily: 'monospace', fontWeight: 600 }}>
                          {formatPrice(technical.support)}
                        </span>
                      </div>
                    )}
                    {technical.resistance != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Direnç</span>
                        <span style={{ color: 'var(--red-400)', fontFamily: 'monospace', fontWeight: 600 }}>
                          {formatPrice(technical.resistance)}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                {technical.stop_loss == null && technical.target_price == null && technical.support == null && technical.resistance == null && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Risk verisi bulunamadı</p>
                )}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Veri bekleniyor...</p>
            )}
          </div>
        </div>

        {/* ── Bottom Grid: Signals + KAP (2 columns) ─── */}
        <div className={styles.bottomGrid}>
          {/* Sol: Teknik Sinyaller */}
          <div className={styles.glassCard}>
            <h3 className={styles.sectionTitle} style={{ marginBottom: 12 }}>Teknik Sinyaller</h3>
            {technical && technical.signals.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {technical.signals.slice(0, 6).map((signal, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      background: signal.direction === 'bullish'
                        ? 'rgba(34,197,94,0.1)'
                        : signal.direction === 'bearish'
                          ? 'rgba(239,68,68,0.1)'
                          : 'rgba(148,163,184,0.1)',
                      color: signal.direction === 'bullish'
                        ? 'var(--green-500)'
                        : signal.direction === 'bearish'
                          ? 'var(--red-500)'
                          : 'var(--text-muted)',
                    }}>
                      {signal.direction === 'bullish' ? '▲' : signal.direction === 'bearish' ? '▼' : '●'}
                    </span>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', flex: 1 }}>
                      {signal.name}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {(signal.strength * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Aktif sinyal bulunamadı</p>
            )}
          </div>

          {/* Sag: KAP Bildirimleri */}
          <div className={styles.glassCard}>
            <KAPNewsCard news={kapNews} loading={newsLoading} />
          </div>
        </div>

        {/* ── Temel Bilgiler (info panel) ────────────── */}
        <div className={styles.glassCard} style={{ marginTop: 20 }}>
          <h3 className={styles.sectionTitle}>Temel Bilgiler</h3>
          <div className={styles.infoGrid}>
            <InfoItem label="Piyasa Değeri" value={formatMarketCap(s.market_cap)} />
            <InfoItem label="Hacim" value={formatVolume(s.volume)} />
            <InfoItem label="Sektör" value={s.sector || '—'} />
            <InfoItem label="Alt Sektör" value={s.industry || '—'} />
            <InfoItem label="Para Birimi" value={s.currency || 'TRY'} />
            <InfoItem label="Son Güncelleme" value={s.last_data_update ? new Date(s.last_data_update).toLocaleDateString('tr-TR') : '—'} />
          </div>
        </div>
      </TerminalShell>
    </AppShell>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.infoItem}>
      <span className={styles.infoLabel}>{label}</span>
      <span className={styles.infoValue}>{value}</span>
    </div>
  );
}
