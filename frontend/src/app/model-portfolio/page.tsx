'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { formatPrice } from '@/components/StockHelpers';
import api, {
  ModelPortfolioCurrentResponse,
  ModelPortfolioHolding,
  ModelPortfolioWeekSummary,
} from '@/lib/api';
import styles from './page.module.css';

// ── Helpers ──────────────────────────────────────────────────

function formatWeekRange(weekStart: string, weekEnd: string): string {
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'long', year: 'numeric' };
  const start = new Date(weekStart).toLocaleDateString('tr-TR', opts);
  const end = new Date(weekEnd).toLocaleDateString('tr-TR', opts);
  return `${start} – ${end}`;
}

function formatPct(value: number | null | undefined, showPlus = true): string {
  if (value === null || value === undefined) return '—';
  const sign = value >= 0 && showPlus ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function scoreColor(score: number | null): string {
  if (score === null) return 'var(--text-muted)';
  if (score >= 70) return 'var(--accent-green)';
  if (score >= 50) return 'var(--accent)';
  return 'var(--accent-red)';
}

// ── Sub Components ──────────────────────────────────────────

function SkeletonRow() {
  return (
    <tr className={styles.skeletonRow}>
      {Array.from({ length: 9 }).map((_, i) => (
        <td key={i}><span className={styles.skeletonCell} /></td>
      ))}
    </tr>
  );
}

function HeroCard({ week }: { week: ModelPortfolioWeekSummary }) {
  const portfolioReturn = week.portfolio_return_pct;
  const benchmarkReturn = week.benchmark_return_pct;
  const activeSpread = week.active_return_spread;
  const isPositive = (portfolioReturn ?? 0) >= 0;

  return (
    <div className={styles.heroCard}>
      <div className={styles.heroWeek}>
        {formatWeekRange(week.week_start, week.week_end)}
      </div>
      <div className={styles.heroMetrics}>
        <div className={styles.heroMain}>
          <span
            className={styles.heroReturn}
            style={{ color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}
          >
            {formatPct(portfolioReturn)}
          </span>
          <span className={styles.heroLabel}>Portföy Getirisi</span>
        </div>
        <div className={styles.heroDivider} />
        <div className={styles.heroStat}>
          <span className={styles.heroStatValue}>{formatPct(benchmarkReturn)}</span>
          <span className={styles.heroStatLabel}>BIST100</span>
        </div>
        <div className={styles.heroStat}>
          <span
            className={styles.heroStatValue}
            style={{
              color: (activeSpread ?? 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
            }}
          >
            {formatPct(activeSpread)}
          </span>
          <span className={styles.heroStatLabel}>Aktif Getiri</span>
        </div>
        <div className={styles.heroStat}>
          <span className={styles.statusBadge} data-status={week.status.toLowerCase()}>
            {week.status}
          </span>
          <span className={styles.heroStatLabel}>Durum</span>
        </div>
      </div>
    </div>
  );
}

function AllocationBar({ pct }: { pct: number }) {
  return (
    <div className={styles.allocationWrap}>
      <div className={styles.allocationBar}>
        <div className={styles.allocationFill} style={{ width: `${Math.min(pct * 5, 100)}%` }} />
      </div>
      <span className={styles.allocationLabel}>{pct.toFixed(1)}%</span>
    </div>
  );
}

function HoldingRow({ holding }: { holding: ModelPortfolioHolding }) {
  const weeklyReturn = holding.weekly_return_pct ?? 0;
  const isGreen = weeklyReturn >= 0;

  return (
    <Link href={`/stocks/${holding.symbol}`} className={styles.holdingRow}>
      <span className={styles.rank}>{holding.rank}</span>
      <span className={styles.symbol}>{holding.symbol}</span>
      <span className={styles.name} title={holding.name ?? ''}>
        {holding.name ?? '—'}
      </span>
      <span className={styles.sector}>{holding.sector ?? '—'}</span>
      <span className={styles.allocation}>
        <AllocationBar pct={holding.allocation_pct} />
      </span>
      <span className={styles.price}>{formatPrice(holding.entry_price)}</span>
      <span className={styles.price}>{formatPrice(holding.current_price)}</span>
      <span
        className={styles.weeklyReturn}
        style={{ color: isGreen ? 'var(--accent-green)' : 'var(--accent-red)' }}
      >
        {formatPct(holding.weekly_return_pct)}
      </span>
      <span className={styles.score} style={{ color: scoreColor(holding.overall_score) }}>
        {holding.overall_score !== null ? holding.overall_score.toFixed(1) : '—'}
      </span>
    </Link>
  );
}

function GenerationNotesCard({
  data,
}: {
  data: NonNullable<ModelPortfolioCurrentResponse['generation_notes']>;
}) {
  return (
    <div className={styles.notesCard}>
      {data.selection_rule && (
        <p className={styles.notesRule}>
          <span className={styles.notesKey}>Seçim kuralı:</span> {data.selection_rule}
        </p>
      )}
      {data.penalized_symbols.length > 0 && (
        <p className={styles.notesItem}>
          <span className={styles.notesKey}>Ceza uygulanan hisseler:</span>{' '}
          {data.penalized_symbols.join(', ')}
        </p>
      )}
      {data.previous_adjustment_mode && (
        <p className={styles.notesItem}>
          <span className={styles.notesKey}>Önceki mod:</span> {data.previous_adjustment_mode}
        </p>
      )}
      {data.previous_review_summary && (
        <p className={styles.notesItem}>{data.previous_review_summary}</p>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────

export default function ModelPortfolioPage() {
  const [data, setData] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getCurrentModelPortfolio();
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model portföy yüklenemedi');
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const response = await api.generateModelPortfolio(false);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model portföy oluşturulamadı');
    } finally {
      setGenerating(false);
    }
  }

  const week = data?.week ?? null;
  const holdings = data?.holdings ?? [];
  const generationNotes = data?.generation_notes ?? null;
  const hasPortfolio = holdings.length > 0;

  return (
    <AppShell>
      <div className={styles.page}>

        {/* ── Page Header ── */}
        <div className={styles.header}>
          <span className={styles.eyebrow}>AI · HAFTALIK SEÇİM</span>
          <h1 className={styles.title}>Model Portföy</h1>
          <p className={styles.subtitle}>
            AI tarafından haftalık olarak güncellenen, temel ve teknik analize dayalı portföy.
          </p>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className={styles.errorBanner}>
            {error}
          </div>
        )}

        {/* ── Hero Summary Card ── */}
        {!loading && week && <HeroCard week={week} />}

        {/* ── Holdings Table ── */}
        <div className={styles.tableSection}>
          <div className={styles.tableHeader}>
            <div className={styles.tableColSira}>Sıra</div>
            <div className={styles.tableColSymbol}>Sembol</div>
            <div className={styles.tableColName}>Şirket</div>
            <div className={styles.tableColSector}>Sektör</div>
            <div className={styles.tableColWeight}>Ağırlık</div>
            <div className={styles.tableColPrice}>Giriş</div>
            <div className={styles.tableColPrice}>Son Fiyat</div>
            <div className={styles.tableColReturn}>Haftalık Getiri</div>
            <div className={styles.tableColScore}>Skor</div>
          </div>

          {loading ? (
            <table className={styles.skeletonTable}>
              <tbody>
                {Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}
              </tbody>
            </table>
          ) : hasPortfolio ? (
            <div className={styles.holdingsList}>
              {holdings.map((holding) => (
                <HoldingRow key={holding.id} holding={holding} />
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <p className={styles.emptyText}>Model portföy henüz oluşturulmadı.</p>
              <button
                className={styles.generateBtn}
                onClick={handleGenerate}
                disabled={generating}
              >
                {generating ? 'Oluşturuluyor...' : 'Oluştur'}
              </button>
            </div>
          )}
        </div>

        {/* ── Generation Notes ── */}
        {!loading && generationNotes && (
          <div className={styles.notesSection}>
            <h2 className={styles.notesSectionTitle}>Oluşturma Notları</h2>
            <GenerationNotesCard data={generationNotes} />
          </div>
        )}

      </div>
    </AppShell>
  );
}
