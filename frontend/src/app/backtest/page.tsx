'use client';

/**
 * Backtest & Sinyal Performans Sayfası
 * Geçmiş sinyal kararlarının hit ratio ve getiri tablosu.
 * BACKTEST-01..04
 */

import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import api, {
  SignalOutcomeItem,
  SignalOutcomesResponse,
  SignalCalibrationResponse,
} from '@/lib/api';
import styles from './backtest.module.css';

// ── Sabitler ────────────────────────────────────────────────

// Dönem filtresi: label -> limit eşlemesi (BACKTEST-02)
const PERIOD_OPTIONS = [
  { label: '1A', limit: 30 },
  { label: '3A', limit: 90 },
  { label: '6A', limit: 180 },
] as const;

type PeriodLabel = (typeof PERIOD_OPTIONS)[number]['label'];

// action -> DB recommendation string
const ACTION_TO_REC: Record<string, string> = {
  strong_buy: 'GÜÇLÜ AL',
  buy: 'AL',
  watch: 'TUT',
  hold: 'TUT',
  reduce: 'SAT',
  exit: 'GÜÇLÜ SAT',
};

// DB recommendation -> kullanıcıya gösterilen güvenli etiket (KARAR-01)
const SAFE_LABEL_MAP: Record<string, string> = {
  'GÜÇLÜ AL': 'Yüksek Öncelikli İzleme',
  'AL': 'Pozitif Görünüm',
  'TUT': 'Nötr İzleme',
  'SAT': 'Zayıflayan Görünüm',
  'GÜÇLÜ SAT': 'Riskli Görünüm',
};

// Filtre'de görünen etiket seçenekleri (BACKTEST-02)
const ACTION_FILTER_OPTIONS = [
  { label: 'Tümü', value: '' },
  { label: 'Yüksek Öncelikli İzleme', value: 'strong_buy' },
  { label: 'Pozitif Görünüm', value: 'buy' },
  { label: 'Nötr İzleme', value: 'watch' },
  { label: 'Zayıflayan Görünüm', value: 'reduce' },
  { label: 'Riskli Görünüm', value: 'exit' },
];

// Başarı durumu filtre seçenekleri (BACKTEST-02)
const OUTCOME_FILTER_OPTIONS = [
  { label: 'Tümü', value: '' },
  { label: 'Başarılı', value: 'success' },
  { label: 'Başarısız', value: 'failure' },
  { label: 'Beklemede', value: 'pending' },
];

// ── Yardımcı fonksiyonlar ────────────────────────────────────

function fmtPct(v: number | null): string {
  if (v === null) return '—';
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
}

function labelColor(action: string): string {
  if (action === 'strong_buy' || action === 'buy') return 'var(--accent-green)';
  if (action === 'exit' || action === 'reduce') return 'var(--accent-red)';
  return 'var(--accent)';
}

function returnColor(v: number | null): string {
  if (v === null) return 'var(--text-muted)';
  return v > 0 ? 'var(--accent-green)' : 'var(--accent-red)';
}

// ── Sayfa ────────────────────────────────────────────────────

export default function BacktestPage() {
  const [outcomes, setOutcomes] = useState<SignalOutcomeItem[]>([]);
  const [summary, setSummary] = useState<SignalOutcomesResponse['summary'] | null>(null);
  const [calibration, setCalibration] = useState<SignalCalibrationResponse | null>(null);
  const [calibration1m, setCalibration1m] = useState<SignalCalibrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<PeriodLabel>('3A');
  const [actionFilter, setActionFilter] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('');

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const limitMap: Record<PeriodLabel, number> = { '1A': 30, '3A': 90, '6A': 180 };
      const limit = limitMap[period] ?? 90;
      const [outcomesRes, calibRes, calibRes1m] = await Promise.all([
        api.getSignalOutcomes(limit, '1w'),
        api.getSignalCalibration('1w', 1),
        api.getSignalCalibration('1m', 1),
      ]);
      setOutcomes(outcomesRes.items);
      setSummary(outcomesRes.summary);
      setCalibration(calibRes);
      setCalibration1m(calibRes1m);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Veri yüklenemedi');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  // İstemci tarafı filtreleme (BACKTEST-02)
  const filtered = outcomes.filter((item) => {
    if (actionFilter && item.action !== actionFilter) return false;
    if (outcomeFilter === 'success' && item.outcome_1w !== 'success') return false;
    if (outcomeFilter === 'failure' && item.outcome_1w !== 'failure') return false;
    if (outcomeFilter === 'pending' && item.outcome_1w !== null) return false;
    return true;
  });

  // KPI hesaplamaları (BACKTEST-03)
  const totalSignals = outcomes.length;
  const successRate1w = calibration?.overall.success_rate ?? null;
  const avgReturn1w = calibration?.overall.avg_return_pct ?? null;
  const avgReturn1m = calibration1m?.overall.avg_return_pct ?? null;

  return (
    <AppShell>
      <div className={styles.container}>
        {/* Başlık */}
        <div className={styles.header}>
          <h1 className={styles.title}>Sinyal Performansı</h1>
          <p className={styles.subtitle}>
            Geçmiş sinyal kararlarının gerçekleşen getiri ve başarı oranları
          </p>
        </div>

        {/* Hata mesajı */}
        {error && <div className={styles.error}>{error}</div>}

        {/* KPI Kartlar (BACKTEST-03) */}
        <div className={styles.kpiGrid}>
          <div className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Toplam Sinyal</p>
            <p className={styles.kpiValue}>{loading ? '…' : totalSignals}</p>
            <p className={styles.kpiSub}>Seçili dönem</p>
          </div>
          <div className={styles.kpiCard}>
            <p className={styles.kpiLabel}>1H Başarı Oranı</p>
            <p
              className={styles.kpiValue}
              style={{
                color:
                  successRate1w === null
                    ? 'var(--text)'
                    : successRate1w >= 60
                    ? 'var(--accent-green)'
                    : 'var(--accent-red)',
              }}
            >
              {loading ? '…' : successRate1w !== null ? `%${successRate1w.toFixed(1)}` : '—'}
            </p>
            <p className={styles.kpiSub}>1 haftalık ufuk</p>
          </div>
          <div className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Ort. 1H Getiri</p>
            <p
              className={styles.kpiValue}
              style={{ color: returnColor(avgReturn1w) }}
            >
              {loading ? '…' : fmtPct(avgReturn1w)}
            </p>
            <p className={styles.kpiSub}>Ortalama hisse getirisi</p>
          </div>
          <div className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Ort. 1M Getiri</p>
            <p
              className={styles.kpiValue}
              style={{ color: returnColor(avgReturn1m) }}
            >
              {loading ? '…' : fmtPct(avgReturn1m)}
            </p>
            <p className={styles.kpiSub}>Ortalama 1 aylık getiri</p>
          </div>
        </div>

        {/* Filtre Bar (BACKTEST-02) */}
        <div className={styles.filterBar}>
          {/* Dönem filtresi */}
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Dönem:</span>
            {PERIOD_OPTIONS.map((p) => (
              <button
                key={p.label}
                className={`${styles.filterBtn} ${period === p.label ? styles.filterBtnActive : ''}`}
                onClick={() => setPeriod(p.label)}
              >
                {p.label}
              </button>
            ))}
          </div>
          {/* Güvenli etiket filtresi */}
          <select
            className={styles.filterSelect}
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            {ACTION_FILTER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          {/* Başarı durumu filtresi */}
          <select
            className={styles.filterSelect}
            value={outcomeFilter}
            onChange={(e) => setOutcomeFilter(e.target.value)}
          >
            {OUTCOME_FILTER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          {/* Özet: başarı/başarısız/bekleyen sayıları */}
          {summary && !loading && (
            <div className={styles.summaryBadges}>
              <span className={styles.badgeSuccess}>{summary.success} Başarılı</span>
              <span className={styles.badgeFailure}>{summary.failure} Başarısız</span>
              <span className={styles.badgePending}>{summary.pending} Bekliyor</span>
            </div>
          )}
        </div>

        {/* İçerik: tablo veya boş durum */}
        {loading ? (
          <div className={styles.loading}>Yükleniyor...</div>
        ) : filtered.length === 0 ? (
          /* Boş durum (BACKTEST-04) */
          <div className={styles.emptyState}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={styles.emptyIcon}
            >
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
            <p>Henüz backtest verisi yok — sistem sinyal topluyor</p>
          </div>
        ) : (
          /* 7 sütunlu tablo (BACKTEST-01) */
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Tarih</th>
                  <th>Hisse</th>
                  <th>Güvenli Etiket</th>
                  <th>1H %</th>
                  <th>1M %</th>
                  <th>BIST100 Relatif</th>
                  <th>Başarılı mı</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const rec = ACTION_TO_REC[item.action] ?? item.action_label;
                  const labelText = SAFE_LABEL_MAP[rec] ?? rec;
                  const lblColor = labelColor(item.action);
                  const outcome1wIcon =
                    item.outcome_1w === 'success'
                      ? '✓'
                      : item.outcome_1w === 'failure'
                      ? '✗'
                      : '—';
                  const outcome1wColor =
                    item.outcome_1w === 'success'
                      ? 'var(--accent-green)'
                      : item.outcome_1w === 'failure'
                      ? 'var(--accent-red)'
                      : 'var(--text-muted)';
                  const relative = item.excess_return_1w_pct;

                  return (
                    <tr key={item.id}>
                      <td>
                        {item.decision_date
                          ? new Date(item.decision_date).toLocaleDateString('tr-TR', {
                              day: '2-digit',
                              month: 'short',
                              year: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className={styles.symbolCell}>{item.symbol}</td>
                      <td>
                        <span style={{ color: lblColor }}>{labelText}</span>
                      </td>
                      <td style={{ color: returnColor(item.actual_return_1w_pct) }}>
                        {fmtPct(item.actual_return_1w_pct)}
                      </td>
                      <td style={{ color: returnColor(item.actual_return_1m_pct) }}>
                        {fmtPct(item.actual_return_1m_pct)}
                      </td>
                      <td style={{ color: returnColor(relative) }}>
                        {fmtPct(relative)}
                      </td>
                      <td>
                        <span style={{ color: outcome1wColor, fontWeight: 600 }}>
                          {outcome1wIcon}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
