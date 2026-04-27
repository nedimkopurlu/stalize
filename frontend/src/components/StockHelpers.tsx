'use client';

import React from 'react';
import styles from './StockHelpers.module.css';

interface RecommendationBadgeProps {
  recommendation: string | null;
}

const REC_CONFIG: Record<string, { label: string; className: string }> = {
  'GÜÇLÜ AL': { label: 'GÜÇLÜ AL', className: 'badge badge-green' },
  'AL': { label: 'AL', className: 'badge badge-green' },
  'TUT': { label: 'TUT', className: 'badge badge-amber' },
  'SAT': { label: 'SAT', className: 'badge badge-red' },
  'GÜÇLÜ SAT': { label: 'GÜÇLÜ SAT', className: 'badge badge-red' },
};

export default function RecommendationBadge({ recommendation }: RecommendationBadgeProps) {
  if (!recommendation) {
    return <span className={`badge ${styles.badgeEmpty}`}>—</span>;
  }

  const config = REC_CONFIG[recommendation] || { label: recommendation, className: 'badge badge-blue' };

  return <span className={config.className}>{config.label}</span>;
}

// ── Price Change Display ──────────────────────────────────

export function PriceChange({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-muted font-mono">—</span>;
  }

  const isPositive = value >= 0;
  const arrow = isPositive ? '▲' : '▼';

  return (
    <span className={`${styles.priceChange} ${isPositive ? styles.priceChangePositive : styles.priceChangeNegative}`}>
      {arrow} {isPositive ? '+' : ''}{value.toFixed(2)}%
    </span>
  );
}

// ── Format helpers ────────────────────────────────────────

export function formatPrice(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatVolume(value: number | null): string {
  if (value === null || value === undefined) return '—';
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toLocaleString('tr-TR');
}

export function formatMarketCap(value: number | null): string {
  if (value === null || value === undefined) return '—';
  if (value >= 1_000_000_000_000) return `₺${(value / 1_000_000_000_000).toFixed(1)}T`;
  if (value >= 1_000_000_000) return `₺${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `₺${(value / 1_000_000).toFixed(0)}M`;
  return `₺${value.toLocaleString('tr-TR')}`;
}

export function formatPercentage(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return `${value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}
