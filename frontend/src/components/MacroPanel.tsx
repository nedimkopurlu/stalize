'use client';

import React from 'react';
import type { MacroIndicators } from '@/lib/api';
import styles from './MacroPanel.module.css';

interface MacroPanelProps {
  indicators: MacroIndicators | null;
  loading: boolean;
}

interface IndicatorConfig {
  key: keyof MacroIndicators;
  label: string;
  format: (v: number) => string;
  positiveWhenUp: boolean;
}

const INDICATOR_CONFIG: IndicatorConfig[] = [
  {
    key: 'usdtry',
    label: 'USD/TRY',
    format: (v) => v.toFixed(2),
    positiveWhenUp: false,
  },
  {
    key: 'gold_try',
    label: 'Altin (TRY/g)',
    format: (v) => v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }),
    positiveWhenUp: true,
  },
  {
    key: 'bist100',
    label: 'BIST 100',
    format: (v) => v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }),
    positiveWhenUp: true,
  },
  {
    key: 'interest_rate',
    label: 'Faiz (%)',
    format: (v) => `${v.toFixed(1)}%`,
    positiveWhenUp: false,
  },
  {
    key: 'inflation_rate',
    label: 'Enflasyon (%)',
    format: (v) => `${v.toFixed(1)}%`,
    positiveWhenUp: false,
  },
];

export default function MacroPanel({ indicators, loading }: MacroPanelProps) {
  if (loading) {
    return (
      <div className={styles.macroPanel}>
        {INDICATOR_CONFIG.map((cfg) => (
          <div key={cfg.key} className={`${styles.indicatorCard} ${styles.skeleton}`} />
        ))}
      </div>
    );
  }

  if (!indicators) {
    return (
      <div className={styles.macroPanel}>
        <div className={styles.errorNote}>Makro veriler yuklenemedi</div>
      </div>
    );
  }

  return (
    <div className={styles.macroPanel}>
      {INDICATOR_CONFIG.map((cfg) => {
        const rawValue = indicators[cfg.key];
        const value = typeof rawValue === 'number' ? rawValue : null;
        const asOfKey = `${cfg.key}_as_of` as keyof MacroIndicators;
        const rawAsOf = indicators[asOfKey];
        const asOfValue = typeof rawAsOf === 'string' ? rawAsOf : null;

        return (
          <div key={cfg.key} className={styles.indicatorCard}>
            <div className={styles.indicatorLabel}>{cfg.label}</div>
            <div className={styles.indicatorValue}>
              {value !== null ? cfg.format(value) : '\u2014'}
            </div>
            <div className={styles.indicatorMeta}>
              {asOfValue ? new Date(asOfValue).toLocaleDateString('tr-TR') : 'Canlı akış bekleniyor'}
            </div>
          </div>
        );
      })}
      <div className={styles.asOf}>
        {indicators.as_of
          ? `Guncellendi: ${new Date(indicators.as_of).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`
          : ''}
      </div>
    </div>
  );
}
