'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import BistComparisonChart from '@/components/BistComparisonChart';
import PerformanceCalendar from '@/components/PerformanceCalendar';
import { TerminalEmpty, TerminalError, TerminalKpiList, TerminalKpiRow, TerminalMetric, TerminalPageHeader, TerminalSection, TerminalShell } from '@/components/TerminalPrimitives';
import terminalStyles from '@/components/terminal.module.css';
import api, { PortfolioHistoryResponse, PortfolioPosition } from '@/lib/api';
import styles from '../model-portfolio/portfolio.module.css';

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '-';
  return `%${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

const INITIAL_FORM = {
  symbol: '',
  entry_price: '',
  quantity: '',
  entry_date: new Date().toISOString().slice(0, 10),
  stop_loss: '',
  target_price: '',
  rationale: '',
};

export default function PortfolioPage() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [history, setHistory] = useState<PortfolioHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(INITIAL_FORM);

  useEffect(() => {
    void loadPortfolio();
  }, []);

  async function loadPortfolio() {
    setLoading(true);
    setError(null);
    try {
      const [positionsRes, historyRes] = await Promise.all([
        api.getPortfolioPositions(),
        api.getPortfolioHistory(180),
      ]);
      setPositions(positionsRes);
      setHistory(historyRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Portföy verisi alınamadı');
    } finally {
      setLoading(false);
    }
  }

  async function submitPosition(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.addPosition({
        symbol: form.symbol.toUpperCase().trim(),
        entry_price: Number(form.entry_price),
        quantity: Number(form.quantity),
        entry_date: form.entry_date,
        stop_loss: form.stop_loss ? Number(form.stop_loss) : undefined,
        target_price: form.target_price ? Number(form.target_price) : undefined,
        rationale: form.rationale || undefined,
      });
      setForm(INITIAL_FORM);
      await loadPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pozisyon eklenemedi');
    } finally {
      setSaving(false);
    }
  }

  async function closePosition(positionId: number) {
    setSaving(true);
    setError(null);
    try {
      await api.closePosition(positionId);
      await loadPortfolio();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pozisyon kapatılamadı');
    } finally {
      setSaving(false);
    }
  }

  const investedValue = positions.reduce((sum, pos) => sum + pos.entry_price * pos.quantity, 0);
  const currentValue = positions.reduce((sum, pos) => sum + (pos.current_price ?? pos.entry_price) * pos.quantity, 0);
  const totalPnlPct = investedValue > 0 ? ((currentValue - investedValue) / investedValue) * 100 : null;
  const snapshots = history?.snapshots ?? [];
  const riskSummary = history?.risk_summary;

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Portföyüm"
          description="Kişisel pozisyonlarını ekle, kapat, benchmark farkını ve günlük performansı aynı yerde takip et."
          action={(
            <button className="btn btn-primary" onClick={loadPortfolio} disabled={loading || saving}>
              {loading ? 'Yükleniyor...' : 'Portföyü Yenile'}
            </button>
          )}
        />
        {error ? <TerminalError>{error}</TerminalError> : null}

        <div className={terminalStyles.metricGrid}>
          <TerminalMetric label="Aktif Pozisyon" value={positions.length} note="Açık pozisyon sayısı" />
          <TerminalMetric label="Güncel Değer" value={formatCurrency(currentValue)} note="Portföy piyasa değeri" />
          <TerminalMetric label="Toplam P&L" value={formatPercent(totalPnlPct)} note="Açık pozisyon getirisi" />
          <TerminalMetric label="Riskte Pozisyon" value={riskSummary?.positions_at_risk ?? 0} note="Stop seviyesine yaklaşan" />
          <TerminalMetric label="Hedefe Yakın" value={riskSummary?.positions_near_target ?? 0} note="Hedefe yaklaşanlar" />
          <TerminalMetric label="Benchmark Farkı" value={formatPercent(history?.comparison.active_return_spread)} note="BIST100 göreli getiri" />
        </div>

        <TerminalSection title="Pozisyon Ekle" description="Portföyünü buradan manuel yönet">
          <form onSubmit={submitPosition} className={styles.positionForm}>
            <div className={styles.formGridFour}>
              <input className="search-input" placeholder="Sembol" value={form.symbol} onChange={(e) => setForm((prev) => ({ ...prev, symbol: e.target.value }))} required />
              <input className="search-input" placeholder="Giriş Fiyatı" type="number" step="0.01" value={form.entry_price} onChange={(e) => setForm((prev) => ({ ...prev, entry_price: e.target.value }))} required />
              <input className="search-input" placeholder="Adet" type="number" step="0.01" value={form.quantity} onChange={(e) => setForm((prev) => ({ ...prev, quantity: e.target.value }))} required />
              <input className="search-input" type="date" value={form.entry_date} onChange={(e) => setForm((prev) => ({ ...prev, entry_date: e.target.value }))} required />
            </div>
            <div className={styles.formGridThree}>
              <input className="search-input" placeholder="Stop Loss" type="number" step="0.01" value={form.stop_loss} onChange={(e) => setForm((prev) => ({ ...prev, stop_loss: e.target.value }))} />
              <input className="search-input" placeholder="Hedef Fiyat" type="number" step="0.01" value={form.target_price} onChange={(e) => setForm((prev) => ({ ...prev, target_price: e.target.value }))} />
              <input className="search-input" placeholder="Gerekçe" value={form.rationale} onChange={(e) => setForm((prev) => ({ ...prev, rationale: e.target.value }))} />
            </div>
            <div className={styles.formActions}>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? 'Kaydediliyor...' : 'Pozisyonu Ekle'}
              </button>
            </div>
          </form>
        </TerminalSection>

        {history ? (
          <div className={styles.chartGrid}>
            <BistComparisonChart
              portfolioSeries={history.comparison.portfolio_series}
              benchmarkSeries={history.comparison.benchmark_series}
              benchmarkLabel={history.comparison.benchmark_label}
            />
            <TerminalSection title="Risk Özeti" description="Kişisel portföy gerilim seviyesi" muted>
              <TerminalKpiList>
                <TerminalKpiRow label="Hedefe Yakın" value={`${riskSummary?.positions_near_target ?? 0} pozisyon`} />
                <TerminalKpiRow label="Riskte" value={`${riskSummary?.positions_at_risk ?? 0} pozisyon`} />
                <TerminalKpiRow label="Portföy Getirisi" value={formatPercent(riskSummary?.latest_portfolio_return_pct)} />
                <TerminalKpiRow label="BIST100 Getirisi" value={formatPercent(riskSummary?.latest_benchmark_return_pct)} />
              </TerminalKpiList>
            </TerminalSection>
          </div>
        ) : null}

        <TerminalSection title="Pozisyonlar" description="Kişisel portföyündeki aktif hisseler">
          {positions.length === 0 ? (
            <TerminalEmpty>Henüz kişisel portföyünde aktif pozisyon yok.</TerminalEmpty>
          ) : (
            <div className={styles.tableWrap}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th>Giriş</th>
                    <th>Güncel</th>
                    <th>Adet</th>
                    <th>P&amp;L</th>
                    <th>Stop / Hedef</th>
                    <th>Gerekçe</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.id}>
                      <td style={{ fontWeight: 800 }}>{pos.symbol}</td>
                      <td>{formatCurrency(pos.entry_price)}</td>
                      <td>{formatCurrency(pos.current_price)}</td>
                      <td>{pos.quantity}</td>
                      <td style={{ fontWeight: 800, color: (pos.pnl_pct ?? 0) >= 0 ? 'var(--green-400)' : 'var(--red-400)' }}>
                        {formatPercent(pos.pnl_pct)}
                      </td>
                      <td>{formatCurrency(pos.stop_loss)} / {formatCurrency(pos.target_price)}</td>
                      <td className="text-secondary">{pos.rationale || '-'}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm" onClick={() => void closePosition(pos.id)} disabled={saving}>
                          Kapat
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TerminalSection>

        <TerminalSection title="Günlük Takip" description="Portföy snapshot takvimi">
          <PerformanceCalendar snapshots={snapshots} />
        </TerminalSection>
      </TerminalShell>
    </AppShell>
  );
}
