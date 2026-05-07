'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import api, { ModelPortfolioCurrentResponse } from '@/lib/api';
import styles from './page.module.css';

// ── Static Strategy Data ─────────────────────────────────────

interface Strategy {
  id: string;
  tag: string;
  tagColor: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  return1y: string;
  returnYtd: string;
  risk: string;
  returnPositive: boolean;
  ytdPositive: boolean;
  holdings: string[];
}

const STRATEGIES: Strategy[] = [
  {
    id: 'temettü',
    tag: 'KONSERVATİF',
    tagColor: '#10b981',
    name: 'Temettü Avcısı',
    description: 'Yüksek temettü verimi ve istikrarlı nakit akışı sunan köklü BIST şirketlerine odaklanır.',
    icon: '◐',
    color: '#10b981',
    return1y: '+18.4%',
    returnYtd: '+6.2%',
    risk: 'Düşük',
    returnPositive: true,
    ytdPositive: true,
    holdings: ['GARAN', 'TUPRS', 'KCHOL', 'AKBNK', 'TCELL'],
  },
  {
    id: 'büyüme',
    tag: 'AGRESİF',
    tagColor: '#f59e0b',
    name: 'Büyüme Lokomotifleri',
    description: 'Güçlü büyüme ivmesi ve yüksek momentum gösteren sektör liderlerine yatırım yapar.',
    icon: '◆',
    color: '#f59e0b',
    return1y: '+42.6%',
    returnYtd: '+18.8%',
    risk: 'Yüksek',
    returnPositive: true,
    ytdPositive: true,
    holdings: ['ASELS', 'THYAO', 'FROTO', 'PGSUS', 'TOASO'],
  },
  {
    id: 'defansif',
    tag: 'DENGELİ',
    tagColor: '#3b82f6',
    name: 'Defansif Bankacılık',
    description: 'Bankacılık sektörünün kaliteli isimlerini dengeli ağırlıklarla portföyde tutar.',
    icon: '◈',
    color: '#3b82f6',
    return1y: '+24.8%',
    returnYtd: '+9.4%',
    risk: 'Orta',
    returnPositive: true,
    ytdPositive: true,
    holdings: ['GARAN', 'AKBNK', 'YKBNK', 'ISCTR'],
  },
  {
    id: 'yeni-türkiye',
    tag: 'TEMATİK',
    tagColor: '#a855f7',
    name: 'Yeni Türkiye',
    description: 'Türkiye\'nin yapısal dönüşümünden en çok yararlanan savunma, ulaşım ve sanayi şirketleri.',
    icon: '◉',
    color: '#a855f7',
    return1y: '+36.2%',
    returnYtd: '+14.6%',
    risk: 'Orta-Yüksek',
    returnPositive: true,
    ytdPositive: true,
    holdings: ['ASELS', 'THYAO', 'PGSUS', 'FROTO'],
  },
  {
    id: 'değer',
    tag: 'KLASİK',
    tagColor: '#f43f5e',
    name: 'Değer Yatırımcısı',
    description: 'Düşük fiyat/kazanç oranı ve güçlü bilanço ile işlem gören holding ve sanayi devleri.',
    icon: '○',
    color: '#f43f5e',
    return1y: '+16.2%',
    returnYtd: '+4.8%',
    risk: 'Düşük-Orta',
    returnPositive: true,
    ytdPositive: true,
    holdings: ['SAHOL', 'KCHOL', 'EREGL', 'SISE', 'TUPRS'],
  },
  {
    id: 'endeks',
    tag: 'ENDEKS',
    tagColor: '#0ea5e9',
    name: 'BIST 30 Pasif',
    description: 'BIST 30 endeksini taklit eden düşük maliyetli pasif strateji. Piyasa getirisini hedefler.',
    icon: '◇',
    color: '#0ea5e9',
    return1y: '+21.4%',
    returnYtd: '+7.8%',
    risk: 'Piyasa',
    returnPositive: true,
    ytdPositive: true,
    holdings: [],
  },
];

// ── Helpers ──────────────────────────────────────────────────

function formatPct(value: number | null | undefined, showPlus = true): string {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 && showPlus ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

// ── Sub Components ────────────────────────────────────────────

function StrategyCard({ strategy }: { strategy: Strategy }) {
  const iconBg = `${strategy.color}22`;

  return (
    <div className={styles.card}>
      {/* Card header */}
      <div className={styles.cardHeader}>
        <div
          className={styles.iconCircle}
          style={{ background: iconBg, color: strategy.color }}
        >
          {strategy.icon}
        </div>
        <span
          className={styles.tag}
          style={{ color: strategy.tagColor, borderColor: `${strategy.tagColor}44`, background: `${strategy.tagColor}11` }}
        >
          {strategy.tag}
        </span>
      </div>

      {/* Name */}
      <h3 className={styles.cardName}>{strategy.name}</h3>

      {/* Description */}
      <p className={styles.cardDesc}>{strategy.description}</p>

      {/* Stats row */}
      <div className={styles.statsRow}>
        <div className={styles.statItem}>
          <span
            className={styles.statValue}
            style={{ color: strategy.returnPositive ? 'var(--accent-green, #10b981)' : 'var(--accent-red, #ef4444)' }}
          >
            {strategy.return1y}
          </span>
          <span className={styles.statLabel}>1Y Getiri</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span
            className={styles.statValue}
            style={{ color: strategy.ytdPositive ? 'var(--accent-green, #10b981)' : 'var(--accent-red, #ef4444)' }}
          >
            {strategy.returnYtd}
          </span>
          <span className={styles.statLabel}>YBB</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statValue} style={{ color: 'var(--text-primary, #f5f5f7)' }}>
            {strategy.risk}
          </span>
          <span className={styles.statLabel}>Risk</span>
        </div>
      </div>

      {/* Holdings chips */}
      {strategy.holdings.length > 0 ? (
        <div className={styles.holdingsRow}>
          {strategy.holdings.map((sym) => (
            <Link key={sym} href={`/stocks/${sym}`} className={styles.holdingChip}>
              {sym}
            </Link>
          ))}
        </div>
      ) : (
        <div className={styles.holdingsRow}>
          <span className={styles.holdingChipMuted}>Tüm BIST 30 hisseleri</span>
        </div>
      )}

      {/* Action buttons */}
      <div className={styles.cardActions}>
        <button className={styles.btnGhost}>İncele</button>
        <button
          className={styles.btnAccent}
          style={{
            background: strategy.color,
            color: '#fff',
          }}
        >
          Kopyala
        </button>
      </div>
    </div>
  );
}

function AiPortfolioSection() {
  const [data, setData] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  }, []);

  const holdings = data?.holdings ?? [];

  return (
    <section className={styles.aiSection}>
      <div className={styles.aiSectionHeader}>
        <div className={styles.aiSectionMeta}>
          <span className={styles.eyebrow}>AI · HAFTALIK SEÇİM</span>
          <h2 className={styles.aiSectionTitle}>AI Haftalık Portföy</h2>
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
        <p className={styles.aiEmpty}>AI portföy henüz oluşturulmadı.</p>
      )}

      {!loading && holdings.length > 0 && (
        <>
          <div className={styles.aiHoldings}>
            {holdings.map((h) => {
              const weeklyReturn = h.weekly_return_pct ?? 0;
              const isGreen = weeklyReturn >= 0;
              return (
                <Link key={h.id} href={`/stocks/${h.symbol}`} className={styles.aiHoldingCard}>
                  <span className={styles.aiHoldingSymbol}>{h.symbol}</span>
                  <span className={styles.aiHoldingAlloc}>{h.allocation_pct.toFixed(1)}%</span>
                  {h.weekly_return_pct !== null && (
                    <span
                      className={styles.aiHoldingReturn}
                      style={{ color: isGreen ? 'var(--accent-green, #10b981)' : 'var(--accent-red, #ef4444)' }}
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
                        ? 'var(--accent-green, #10b981)'
                        : 'var(--accent-red, #ef4444)',
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
                        ? 'var(--accent-green, #10b981)'
                        : 'var(--accent-red, #ef4444)',
                    }}
                  >
                    {formatPct(data.week.active_return_spread)}
                  </span>
                </span>
              )}
            </div>
          )}
        </>
      )}
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
          <span className={styles.eyebrow}>AI · HAZIR STRATEJİLER</span>
          <h1 className={styles.title}>Model Portföyler</h1>
          <p className={styles.subtitle}>
            Risk profilinize ve hedeflerinize göre, AI tarafından dinamik olarak yeniden dengelenen profesyonel portföyler.
          </p>
        </div>

        {/* ── Strategy Grid ── */}
        <div className={styles.grid}>
          {STRATEGIES.map((strategy) => (
            <StrategyCard key={strategy.id} strategy={strategy} />
          ))}
        </div>

        {/* ── AI Weekly Portfolio ── */}
        <AiPortfolioSection />

      </div>
    </AppShell>
  );
}
