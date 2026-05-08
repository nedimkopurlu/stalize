'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import api, { ModelPortfolioCurrentResponse, ModelPortfolioHistoryResponse } from '@/lib/api';
import styles from './page.module.css';

// ── Strategy Templates ────────────────────────────────────────

const STRATEGIES = [
  { id: 'temettu',  icon: '💰', name: 'Temettü Avcısı',         desc: 'Yüksek ve istikrarlı temettü ödeyen hisseler; pasif gelir odaklı.',          badge: 'Defansif',   accent: 'var(--accent-green)' },
  { id: 'buyume',   icon: '🚀', name: 'Büyüme Lokomotifleri',   desc: 'Güçlü gelir büyümesi ve pazar payı kazanan sektör liderleri.',                badge: 'Agresif',    accent: 'var(--accent-blue)' },
  { id: 'defansif', icon: '🛡️', name: 'Defansif Kalkan',        desc: 'Dayanıklı tüketim ve kamu hizmetleri; piyasa dalgalanmalarına karşı koruma.', badge: 'Düşük Risk', accent: 'var(--accent-indigo)' },
  { id: 'momentum', icon: '⚡', name: 'Momentum',                desc: 'Son 3-6 ayda güçlü fiyat ivmesi gösteren, trend sürebilecek hisseler.',       badge: 'Aktif',      accent: 'var(--accent)' },
  { id: 'deger',    icon: '📊', name: 'Değer Yatırımı',          desc: 'Düşük F/K ve PD/DD ile gerçek değerinin altında işlem gören hisseler.',       badge: 'Uzun Vade',  accent: 'var(--accent-purple)' },
  { id: 'karma',    icon: '🎯', name: 'Karma',                   desc: 'Temettü, büyüme ve değer unsurlarını dengeleyen çeşitli portföy.',            badge: 'Dengeli',    accent: 'var(--text-muted)' },
] as const;

// ── Helpers ──────────────────────────────────────────────────

function formatPct(value: number | null | undefined, showPlus = true): string {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 && showPlus ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function AiPortfolioSection() {
  const [data, setData] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userReturnPct, setUserReturnPct] = useState<number | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const res = await api.getCurrentModelPortfolio();
        setData(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Yüklenemedi');
      } finally {
        setLoading(false);
      }
    })();
    // Non-blocking: kullanıcı portföy getirisi (MODEL-04)
    api.getPortfolioHistory(30)
      .then((r) => setUserReturnPct(r.risk_summary?.latest_portfolio_return_pct ?? null))
      .catch(() => null);
  }, []);

  const holdings = data?.holdings ?? [];

  return (
    <section className={styles.aiSection}>
      <div className={styles.aiSectionHeader}>
        <div className={styles.aiSectionMeta}>
          <span className={styles.eyebrow}>CANLI MODEL ÇIKTISI</span>
          <h2 className={styles.aiSectionTitle}>Haftalık Model Portföy</h2>
        </div>
        {data?.week && (
          <span className={styles.weekBadge}>
            {new Date(data.week.week_start).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
            {' – '}
            {new Date(data.week.week_end).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}
          </span>
        )}
      </div>

      {loading && (
        <div className={styles.aiSkeleton}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={styles.aiSkeletonChip} />
          ))}
        </div>
      )}

      {error && (
        <div className={styles.aiError}>{error}</div>
      )}

      {!loading && !error && holdings.length === 0 && (
        <div className={styles.aiEmptyState}>
          <div className={styles.aiEmptyIcon}>🤖</div>
          <p className={styles.aiEmptyTitle}>AI portföy henüz oluşturulmadı</p>
          <p className={styles.aiEmpty}>Model portföy her hafta otomatik olarak güncellenir.</p>
        </div>
      )}

      {!loading && holdings.length > 0 && (
        <>
          <div className={styles.aiHoldings}>
            {holdings.map((h, index) => {
              const weeklyReturn = h.weekly_return_pct ?? 0;
              const isGreen = weeklyReturn >= 0;
              return (
                <Link key={`${h.id}-${h.symbol}-${index}`} href={`/stocks/${h.symbol}`} className={styles.aiHoldingCard}>
                  <span className={styles.aiHoldingSymbol}>{h.symbol}</span>
                  <span className={styles.aiHoldingAlloc}>{h.allocation_pct.toFixed(1)}%</span>
                  {h.weekly_return_pct !== null && (
                    <span
                      className={styles.aiHoldingReturn}
                      style={{ color: isGreen ? 'var(--accent-green)' : 'var(--accent-red)' }}
                    >
                      {formatPct(h.weekly_return_pct)}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
          {data?.week && (
            <div className={styles.aiStats}>
              {data.week.portfolio_return_pct !== null && (
                <span className={styles.aiStat}>
                  <span className={styles.aiStatLabel}>Portföy Getirisi</span>
                  <span
                    className={styles.aiStatValue}
                    style={{
                      color: (data.week.portfolio_return_pct ?? 0) >= 0
                        ? 'var(--accent-green)'
                        : 'var(--accent-red)',
                    }}
                  >
                    {formatPct(data.week.portfolio_return_pct)}
                  </span>
                </span>
              )}
              {data.week.benchmark_return_pct !== null && (
                <span className={styles.aiStat}>
                  <span className={styles.aiStatLabel}>BIST100</span>
                  <span className={styles.aiStatValue}>{formatPct(data.week.benchmark_return_pct)}</span>
                </span>
              )}
              {data.week.active_return_spread !== null && (
                <span className={styles.aiStat}>
                  <span className={styles.aiStatLabel}>Aktif Getiri</span>
                  <span
                    className={styles.aiStatValue}
                    style={{
                      color: (data.week.active_return_spread ?? 0) >= 0
                        ? 'var(--accent-green)'
                        : 'var(--accent-red)',
                    }}
                  >
                    {formatPct(data.week.active_return_spread)}
                  </span>
                </span>
              )}
            </div>
          )}

          {/* ── Gemini haftalık gerekçe (LLM-04) ── */}
          {data?.week?.review_summary && (
            <div className={styles.reviewSummary}>
              <span className={styles.reviewSummaryIcon}>✦</span>
              <p className={styles.reviewSummaryText}>{data.week.review_summary}</p>
            </div>
          )}

          {/* ── Getiri karşılaştırması (MODEL-04) ── */}
          <div className={styles.comparisonCard}>
            <div className={styles.comparisonTitle}>Getiri Karşılaştırması</div>
            <div className={styles.comparisonRow}>
              <div className={styles.comparisonCol}>
                <div className={styles.comparisonLabel}>Portföyüm</div>
                <div
                  className={styles.comparisonValue}
                  style={{ color: (userReturnPct ?? 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}
                >
                  {userReturnPct != null ? `${userReturnPct >= 0 ? '+' : ''}${userReturnPct.toFixed(1)}%` : '—'}
                </div>
              </div>
              <div className={styles.comparisonCol}>
                <div className={styles.comparisonLabel}>Model Portföy</div>
                <div
                  className={styles.comparisonValue}
                  style={{ color: (data?.week?.portfolio_return_pct ?? 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}
                >
                  {data?.week?.portfolio_return_pct != null
                    ? `${(data.week.portfolio_return_pct ?? 0) >= 0 ? '+' : ''}${data.week.portfolio_return_pct.toFixed(1)}%`
                    : '—'}
                </div>
              </div>
              <div className={styles.comparisonCol}>
                <div className={styles.comparisonLabel}>BIST100</div>
                <div className={styles.comparisonValue}>
                  {data?.week?.benchmark_return_pct != null
                    ? `${(data.week.benchmark_return_pct ?? 0) >= 0 ? '+' : ''}${data.week.benchmark_return_pct.toFixed(1)}%`
                    : '—'}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

// ── Model Portfolio History (MODEL-03) ─────────────────────────

function ModelPortfolioHistory() {
  const [history, setHistory] = useState<ModelPortfolioHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getModelPortfolioHistory(8)
      .then((r) => setHistory(r))
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  const weeks = history?.weeks ?? [];

  if (loading) return <div className={styles.historyLoading}>Geçmiş yükleniyor…</div>;
  if (weeks.length === 0) return null;

  return (
    <section className={styles.historySection}>
      <h2 className={styles.historySectionTitle}>Geçmiş Haftalar</h2>
      <div className={styles.historyTable}>
        {weeks.map((week, i) => {
          const isGreen = (week.portfolio_return_pct ?? 0) >= 0;
          const bIsGreen = (week.benchmark_return_pct ?? 0) >= 0;
          return (
            <div key={`${week.id}-${i}`} className={styles.historyRow}>
              <span className={styles.historyDate}>
                {new Date(week.week_start).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                {' – '}
                {new Date(week.week_end).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
              </span>
              <span
                className={styles.historyReturn}
                style={{ color: isGreen ? 'var(--accent-green)' : 'var(--accent-red)' }}
              >
                {week.portfolio_return_pct != null
                  ? `${isGreen ? '+' : ''}${week.portfolio_return_pct.toFixed(1)}%`
                  : '—'}
              </span>
              <span
                className={styles.historyBenchmark}
                style={{ color: 'var(--text-muted)' }}
              >
                BIST100: {week.benchmark_return_pct != null
                  ? `${bIsGreen ? '+' : ''}${week.benchmark_return_pct.toFixed(1)}%`
                  : '—'}
              </span>
              {(week.review_summary ?? week.change_summary) && (
                <p className={styles.historyReview}>
                  {week.review_summary ?? week.change_summary}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ── Page ─────────────────────────────────────────────────────

export default function ModelPortfolioPage() {
  return (
    <AppShell>
      <div className={styles.page}>

        {/* ── Page Header ── */}
        <div className={styles.header}>
          <span className={styles.eyebrow}>MODEL PORTFÖY</span>
          <h1 className={styles.title}>Model Portföyler</h1>
        </div>

        <AiPortfolioSection />
        <ModelPortfolioHistory />

        {/* ── Strategy Templates ── */}
        <section className={styles.strategiesSection}>
          <div className={styles.strategiesHeader}>
            <h2 className={styles.strategiesTitle}>Strateji Şablonları</h2>
            <p className={styles.strategiesSub}>Yatırım amacına göre hazırlanmış altı şablon. Yakında tıklanabilir hale gelecek.</p>
          </div>
          <div className={styles.strategyGrid}>
            {STRATEGIES.map((s) => (
              <div key={s.id} className={styles.strategyCard} style={{ borderTopColor: s.accent }}>
                <div className={styles.strategyIcon} aria-hidden="true">{s.icon}</div>
                <div className={styles.strategyName}>{s.name}</div>
                <div className={styles.strategyDesc}>{s.desc}</div>
                <div className={styles.strategyBadge} style={{ color: s.accent }}>{s.badge}</div>
              </div>
            ))}
          </div>
        </section>

      </div>
    </AppShell>
  );
}
