'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { TerminalEmpty, TerminalError, TerminalMetric, TerminalPageHeader, TerminalSection, TerminalShell } from '@/components/TerminalPrimitives';
import terminalStyles from '@/components/terminal.module.css';
import api, { ModelPortfolioCurrentResponse, ModelPortfolioHistoryResponse, PortfolioSnapshot } from '@/lib/api';
import PerformanceCalendar from '@/components/PerformanceCalendar';
import styles from './portfolio.module.css';

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '-';
  return `%${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    maximumFractionDigits: 2,
  }).format(value);
}

export default function ModelPortfolioPage() {
  const [current, setCurrent] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [history, setHistory] = useState<ModelPortfolioHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadModelPortfolio();
  }, []);

  async function loadModelPortfolio() {
    setLoading(true);
    setError(null);
    try {
      const [currentResponse, historyResponse] = await Promise.all([
        api.getCurrentModelPortfolio(),
        api.getModelPortfolioHistory(12),
      ]);
      setCurrent(currentResponse);
      setHistory(historyResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model portföy yüklenemedi');
    } finally {
      setLoading(false);
    }
  }

  async function regenerateModelPortfolio() {
    setGenerating(true);
    setError(null);
    try {
      const payload = await api.generateModelPortfolio(true);
      setCurrent(payload);
      const historyResponse = await api.getModelPortfolioHistory(12);
      setHistory(historyResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model portföy üretilemedi');
    } finally {
      setGenerating(false);
    }
  }

  const week = current?.week;
  const holdings = current?.holdings ?? [];
  const reviewNotes = week?.review_notes;
  const nextWeekPlan = reviewNotes?.next_week_adjustments;
  const changes = current?.changes;
  const decisionBand = current?.decision_band;
  const snapshots = (current?.snapshots ?? []).map<PortfolioSnapshot>((snapshot) => ({
    date: snapshot.date,
    total_value: snapshot.total_return_pct,
    daily_pnl_pct: snapshot.daily_return_pct,
    positions_json: snapshot.positions_json,
  }));

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Model Portföy"
          description="Sistemin haftalık kurduğu portföyü, günlük performansı ve haftalık değerlendirme notlarıyla birlikte izle."
          action={(
            <>
              <button className="btn btn-ghost" onClick={loadModelPortfolio} disabled={loading || generating}>
                Yenile
              </button>
              <button className="btn btn-primary" onClick={regenerateModelPortfolio} disabled={generating}>
                {generating ? 'Üretiliyor...' : 'Bu Haftayı Yeniden Kur'}
              </button>
            </>
          )}
        />
        {error ? <TerminalError>{error}</TerminalError> : null}

        <div className={terminalStyles.metricGrid}>
          <TerminalMetric label="Pozisyon Sayısı" value={current?.summary?.holding_count ?? 0} note="Bu haftaki model portföy" />
          <TerminalMetric label="Haftalık Getiri" value={formatPercent(week?.portfolio_return_pct)} note="Portföy toplam getirisi" />
          <TerminalMetric label="Günlük Değişim" value={formatPercent(week?.daily_return_pct)} note="Son günlük izleme" />
          <TerminalMetric label="Benchmark" value={formatPercent(week?.benchmark_return_pct)} note={week?.benchmark_symbol ?? 'BIST100'} />
          <TerminalMetric label="Aktif Fark" value={formatPercent(week?.active_return_spread)} note="Benchmark üzeri/altı" />
          <TerminalMetric label="En İyi Hisse" value={current?.summary?.best_holding?.symbol ?? '-'} note={formatPercent(current?.summary?.best_holding?.weekly_return_pct)} />
          <TerminalMetric label="En Zayıf Hisse" value={current?.summary?.worst_holding?.symbol ?? '-'} note={formatPercent(current?.summary?.worst_holding?.weekly_return_pct)} />
          <TerminalMetric label="Strateji" value={week?.strategy_version ?? '-'} note="Haftalık seçim motoru" />
        </div>

        <TerminalSection title="Karar Bandı" description="Bu hafta model portföy neden böyle kuruldu?">
          {decisionBand ? (
            <div className={styles.decisionBand}>
              <div className="card">
                <strong>{decisionBand.headline}</strong>
                <p className="text-secondary" style={{ marginTop: 10 }}>{decisionBand.focus}</p>
              </div>
              <div className="card">
                {decisionBand.actions.length ? (
                  <div className={styles.changeList}>
                    {decisionBand.actions.map((item) => (
                      <span key={item} className="text-secondary">{item}</span>
                    ))}
                  </div>
                ) : (
                  <span className="text-secondary">Bu hafta için ek aksiyon notu oluşmadı.</span>
                )}
              </div>
            </div>
          ) : (
            <TerminalEmpty>Önceki hafta verisi biriktiğinde karar bandı burada oluşacak.</TerminalEmpty>
          )}
        </TerminalSection>

        <TerminalSection title="Haftalık Değerlendirme" description="Sistem geçen haftadan ne öğrendi?">
          {week?.review_summary ? (
            <div className="card">
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>{week.review_summary}</p>
              {reviewNotes?.poor_performers?.length ? (
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
                  {reviewNotes.poor_performers.slice(0, 4).map((item) => (
                    <span key={item.symbol} className="badge badge-red">
                      {item.symbol} {formatPercent(item.return_pct)}
                    </span>
                  ))}
                </div>
              ) : null}
              {reviewNotes?.factor_drag?.length ? (
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
                  {reviewNotes.factor_drag.slice(0, 3).map((item) => (
                    <span key={item.factor} className="badge">
                      {item.label}
                    </span>
                  ))}
                </div>
              ) : null}
              {nextWeekPlan ? (
                <div style={{ display: 'grid', gap: 8, marginTop: 16 }}>
                  <span className="text-secondary">
                    Gelecek hafta mod: <strong style={{ color: 'var(--text-primary)' }}>{nextWeekPlan.review_mode}</strong>
                  </span>
                  {nextWeekPlan.penalized_symbols.length ? (
                    <span className="text-secondary">
                      Cezalı hisseler: <strong style={{ color: 'var(--text-primary)' }}>{nextWeekPlan.penalized_symbols.join(', ')}</strong>
                    </span>
                  ) : null}
                  {Object.keys(nextWeekPlan.sector_caps).length ? (
                    <span className="text-secondary">
                      Sıkılaştırılan sektörler:{' '}
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {Object.entries(nextWeekPlan.sector_caps).map(([sector, cap]) => `${sector} (${cap})`).join(', ')}
                      </strong>
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : (
            <TerminalEmpty>Bu hafta için henüz değerlendirme notu oluşmadı.</TerminalEmpty>
          )}
        </TerminalSection>

        <TerminalSection title="Haftalık Değişim Günlüğü" description="Geçen haftaya göre model portföy nasıl güncellendi?">
          {changes ? (
            <div className={styles.changeGrid}>
              <div className="card">
                <p className="text-secondary">{changes.summary}</p>
              </div>
              <div className="card">
                <div className={styles.changeBlock}>
                  <strong>Eklenenler</strong>
                  {changes.added.length ? (
                    <div className={styles.badgeRow}>
                      {changes.added.map((symbol) => (
                        <span key={symbol} className="badge badge-green">{symbol}</span>
                      ))}
                    </div>
                  ) : <span className="text-secondary">Yeni hisse yok.</span>}
                </div>
                <div className={styles.changeBlock}>
                  <strong>Çıkarılanlar</strong>
                  {changes.removed.length ? (
                    <div className={styles.badgeRow}>
                      {changes.removed.map((symbol) => (
                        <span key={symbol} className="badge badge-red">{symbol}</span>
                      ))}
                    </div>
                  ) : <span className="text-secondary">Çıkan hisse yok.</span>}
                </div>
              </div>
              <div className="card">
                <div className={styles.changeBlock}>
                  <strong>Ağırlığı Artanlar</strong>
                  {changes.increased.length ? (
                    <div className={styles.changeList}>
                      {changes.increased.slice(0, 4).map((item) => (
                        <span key={item.symbol} className="text-secondary">
                          <strong style={{ color: 'var(--text-primary)' }}>{item.symbol}</strong> +%{item.delta_pct.toFixed(2)}
                        </span>
                      ))}
                    </div>
                  ) : <span className="text-secondary">Artan ağırlık yok.</span>}
                </div>
                <div className={styles.changeBlock}>
                  <strong>Ağırlığı Azalanlar</strong>
                  {changes.decreased.length ? (
                    <div className={styles.changeList}>
                      {changes.decreased.slice(0, 4).map((item) => (
                        <span key={item.symbol} className="text-secondary">
                          <strong style={{ color: 'var(--text-primary)' }}>{item.symbol}</strong> %{item.delta_pct.toFixed(2)}
                        </span>
                      ))}
                    </div>
                  ) : <span className="text-secondary">Azalan ağırlık yok.</span>}
                </div>
              </div>
            </div>
          ) : (
            <TerminalEmpty>Karşılaştırılacak önceki hafta oluştuğunda değişim günlüğü burada görünecek.</TerminalEmpty>
          )}
        </TerminalSection>

        <TerminalSection title="Bu Haftaki Model Portföy" description="Sistemin otomatik seçtiği hisseler">
          {holdings.length === 0 ? (
            <TerminalEmpty>Henüz model portföy üretilmedi. “Bu Haftayı Yeniden Kur” ile ilk portföyü oluşturabilirsin.</TerminalEmpty>
          ) : (
            <div className={styles.tableWrap}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Sembol</th>
                    <th>Ağırlık</th>
                    <th>Giriş</th>
                    <th>Güncel</th>
                    <th>Haftalık</th>
                    <th>Günlük</th>
                    <th>Skor</th>
                    <th>Gerekçe</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => (
                    <tr key={holding.id}>
                      <td style={{ fontWeight: 700 }}>{holding.rank}</td>
                      <td>
                        <div style={{ display: 'grid', gap: 2 }}>
                          <strong>{holding.symbol}</strong>
                          <span className="text-secondary">{holding.sector || '-'}</span>
                        </div>
                      </td>
                      <td>%{holding.allocation_pct.toFixed(2)}</td>
                      <td>{formatCurrency(holding.entry_price)}</td>
                      <td>{formatCurrency(holding.current_price)}</td>
                      <td style={{ fontWeight: 800, color: (holding.weekly_return_pct ?? 0) >= 0 ? 'var(--green-400)' : 'var(--red-400)' }}>
                        {formatPercent(holding.weekly_return_pct)}
                      </td>
                      <td style={{ fontWeight: 800, color: (holding.daily_change_pct ?? 0) >= 0 ? 'var(--green-400)' : 'var(--red-400)' }}>
                        {formatPercent(holding.daily_change_pct)}
                      </td>
                      <td>{holding.overall_score?.toFixed(1) ?? '-'}</td>
                      <td className="text-secondary">{holding.rationale || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TerminalSection>

        <TerminalSection title="Günlük Takip" description="Haftalık model portföyün günlük izleme yüzeyi">
          <PerformanceCalendar snapshots={snapshots} />
        </TerminalSection>

        <TerminalSection title="Geçmiş Haftalar" description="Her haftanın kapanış performansı">
          {history?.weeks?.length ? (
            <div className={styles.tableWrap}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hafta</th>
                    <th>Portföy</th>
                    <th>Benchmark</th>
                    <th>Fark</th>
                    <th>Not</th>
                    <th>Değişim</th>
                  </tr>
                </thead>
                <tbody>
                  {history.weeks.map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: 700 }}>
                        {new Date(item.week_start).toLocaleDateString('tr-TR')} - {new Date(item.week_end).toLocaleDateString('tr-TR')}
                      </td>
                      <td style={{ color: (item.portfolio_return_pct ?? 0) >= 0 ? 'var(--green-400)' : 'var(--red-400)' }}>{formatPercent(item.portfolio_return_pct)}</td>
                      <td>{formatPercent(item.benchmark_return_pct)}</td>
                      <td style={{ color: (item.active_return_spread ?? 0) >= 0 ? 'var(--green-400)' : 'var(--red-400)' }}>{formatPercent(item.active_return_spread)}</td>
                      <td className="text-secondary">{item.review_summary || '-'}</td>
                      <td className="text-secondary">{item.change_summary || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <TerminalEmpty>Henüz geçmiş hafta kaydı yok.</TerminalEmpty>
          )}
        </TerminalSection>
      </TerminalShell>
    </AppShell>
  );
}
