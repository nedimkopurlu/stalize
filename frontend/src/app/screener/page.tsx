'use client';
import React, { useState, useCallback, useEffect } from 'react';
import AppShell from '@/components/AppShell';
import { TerminalPageHeader, TerminalShell } from '@/components/TerminalPrimitives';
import RecommendationBadge, { PriceChange } from '@/components/StockHelpers';
import api from '@/lib/api';
import Link from 'next/link';

// Types
interface ScreenerFilters {
  sector?: string;
  bist30?: boolean;
  bist100?: boolean;
  bist250?: boolean;
  score_min?: number;
  score_max?: number;
  recommendation?: string;
  pe_ratio_max?: number;
  pb_ratio_max?: number;
  roe_min?: number;
  debt_to_equity_max?: number;
  sort_by?: string;
}

interface ScreenerResult {
  symbol: string;
  name: string;
  sector: string | null;
  current_price: number | null;
  daily_change_pct: number | null;
  market_cap: number | null;
  overall_score: number | null;
  technical_score: number | null;
  fundamental_score: number | null;
  recommendation: string | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  is_bist30: boolean;
  is_bist100: boolean;
  is_bist250: boolean;
}

const TEMPLATES: Array<{ label: string; filters: ScreenerFilters }> = [
  { label: 'Düşük F/K', filters: { pe_ratio_max: 10, score_min: 40 } },
  { label: 'Momentum', filters: { score_min: 70, sort_by: 'technical_score' } },
  { label: 'Güçlü Bilanço', filters: { roe_min: 0.15, debt_to_equity_max: 1.0 } },
  { label: 'Yüksek Temettü', filters: { score_min: 60, recommendation: 'AL' } },
];

export default function ScreenerPage() {
  const [filters, setFilters] = useState<ScreenerFilters>({ sort_by: 'overall_score' });
  const [results, setResults] = useState<ScreenerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [screenError, setScreenError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [sectors, setSectors] = useState<string[]>([]);
  const [savedName, setSavedName] = useState('');

  useEffect(() => {
    api.getStockSectors().then(r => setSectors(r.sectors)).catch((e: unknown) => console.error('Sector load failed:', e));
  }, []);

  const runScreener = useCallback(async (f: ScreenerFilters) => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (f.sector) params.sector = f.sector;
      if (f.bist30) params.bist30 = 'true';
      if (f.bist100) params.bist100 = 'true';
      if (f.bist250) params.bist250 = 'true';
      if (f.score_min != null) params.score_min = String(f.score_min);
      if (f.score_max != null) params.score_max = String(f.score_max);
      if (f.recommendation) params.recommendation = f.recommendation;
      if (f.pe_ratio_max != null) params.pe_ratio_max = String(f.pe_ratio_max);
      if (f.pb_ratio_max != null) params.pb_ratio_max = String(f.pb_ratio_max);
      if (f.roe_min != null) params.roe_min = String(f.roe_min);
      if (f.debt_to_equity_max != null) params.debt_to_equity_max = String(f.debt_to_equity_max);
      if (f.sort_by) params.sort_by = f.sort_by;
      params.limit = '200';

      setScreenError(null);
      const data = await api.screenStocks(params) as { stocks?: ScreenerResult[]; count?: number };
      setResults(data.stocks ?? []);
      setTotal(data.count ?? 0);
    } catch (err) {
      setScreenError(err instanceof Error ? err.message : 'Tarama yapılamadı');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  function applyTemplate(template: ScreenerFilters) {
    const newFilters: ScreenerFilters = { sort_by: 'overall_score', ...template };
    setFilters(newFilters);
    void runScreener(newFilters);
  }

  function saveFilter() {
    if (!savedName.trim()) return;
    const saved = JSON.parse(localStorage.getItem('stalize-screener-presets') ?? '[]') as Array<{ name: string; filters: ScreenerFilters }>;
    saved.push({ name: savedName.trim(), filters });
    localStorage.setItem('stalize-screener-presets', JSON.stringify(saved));
    setSavedName('');
  }

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Tarama Motoru"
          description="Filtrele, sırala, keşfet — 400+ Borsa İstanbul hissesi tek ekranda."
        />

        {/* Template presets */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          {TEMPLATES.map(t => (
            <button
              key={t.label}
              className="btn btn-ghost btn-sm"
              onClick={() => applyTemplate(t.filters)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Filter form */}
        <div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Sektör</label>
              <select
                className="search-input"
                value={filters.sector ?? ''}
                onChange={e => setFilters(f => ({ ...f, sector: e.target.value || undefined }))}
              >
                <option value="">Tüm Sektörler</option>
                {sectors.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Min Skor</label>
              <input
                type="number"
                className="search-input"
                placeholder="0"
                min={0}
                max={100}
                value={filters.score_min ?? ''}
                onChange={e => setFilters(f => ({ ...f, score_min: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Max F/K</label>
              <input
                type="number"
                className="search-input"
                placeholder="Örn: 15"
                min={0}
                value={filters.pe_ratio_max ?? ''}
                onChange={e => setFilters(f => ({ ...f, pe_ratio_max: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Max PD/DD</label>
              <input
                type="number"
                className="search-input"
                placeholder="Örn: 3"
                min={0}
                value={filters.pb_ratio_max ?? ''}
                onChange={e => setFilters(f => ({ ...f, pb_ratio_max: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Min ROE (%)</label>
              <input
                type="number"
                className="search-input"
                placeholder="Örn: 15"
                min={0}
                value={filters.roe_min != null ? filters.roe_min * 100 : ''}
                onChange={e => setFilters(f => ({ ...f, roe_min: e.target.value ? Number(e.target.value) / 100 : undefined }))}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Sinyal</label>
              <select
                className="search-input"
                value={filters.recommendation ?? ''}
                onChange={e => setFilters(f => ({ ...f, recommendation: e.target.value || undefined }))}
              >
                <option value="">Tümü</option>
                <option value="GÜÇLÜ AL">GÜÇLÜ AL</option>
                <option value="AL">AL</option>
                <option value="TUT">TUT</option>
                <option value="SAT">SAT</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Sırala</label>
              <select
                className="search-input"
                value={filters.sort_by ?? 'overall_score'}
                onChange={e => setFilters(f => ({ ...f, sort_by: e.target.value }))}
              >
                <option value="overall_score">Genel Skor</option>
                <option value="technical_score">Teknik Skor</option>
                <option value="fundamental_score">Temel Skor</option>
                <option value="market_cap">Piyasa Değeri</option>
                <option value="daily_change_pct">Günlük Değişim</option>
              </select>
            </div>
          </div>

          {/* Index toggles */}
          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            {(['bist30', 'bist100', 'bist250'] as const).map(key => (
              <button
                key={key}
                className={`btn btn-sm ${filters[key] ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setFilters(f => ({ ...f, [key]: !f[key] || undefined }))}
              >
                {key.toUpperCase()}
              </button>
            ))}
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => void runScreener(filters)}
                disabled={loading}
              >
                {loading ? 'Taranıyor...' : 'Tara'}
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => { setFilters({ sort_by: 'overall_score' }); setResults([]); setTotal(0); }}
              >
                Sıfırla
              </button>
            </div>
          </div>
        </div>

        {/* Save filter */}
        {results.length > 0 && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
            <input
              className="search-input"
              placeholder="Filtre adı..."
              value={savedName}
              onChange={e => setSavedName(e.target.value)}
              style={{ maxWidth: 200 }}
            />
            <button className="btn btn-ghost btn-sm" onClick={saveFilter}>Kaydet</button>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{total} sonuç bulundu</span>
          </div>
        )}

        {screenError && (
          <div style={{ color: 'var(--red-400)', padding: '12px 0', fontWeight: 600 }}>
            Hata: {screenError}
          </div>
        )}

        {/* Results table */}
        {results.length > 0 && (
          <div className="glass-card" style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Hisse</th>
                  <th>Fiyat</th>
                  <th>Değişim</th>
                  <th>Sektör</th>
                  <th>Skor</th>
                  <th>F/K</th>
                  <th>PD/DD</th>
                  <th>ROE</th>
                  <th>Sinyal</th>
                </tr>
              </thead>
              <tbody>
                {results.map(r => (
                  <tr key={r.symbol}>
                    <td>
                      <Link href={`/stocks/${r.symbol}`} style={{ color: 'var(--accent-cyan)', fontWeight: 600, textDecoration: 'none' }}>
                        {r.symbol}
                        {r.is_bist30 && <span style={{ marginLeft: 4, fontSize: '0.6rem', color: 'var(--text-muted)' }}>B30</span>}
                      </Link>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.name?.substring(0, 20)}</div>
                    </td>
                    <td className="font-mono">{r.current_price != null ? r.current_price.toFixed(2) : '—'}</td>
                    <td><PriceChange value={r.daily_change_pct} /></td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.sector ?? '—'}</td>
                    <td className="font-mono" style={{ fontWeight: 600 }}>{r.overall_score != null ? r.overall_score.toFixed(1) : '—'}</td>
                    <td className="font-mono">{r.pe_ratio != null ? r.pe_ratio.toFixed(1) : '—'}</td>
                    <td className="font-mono">{r.pb_ratio != null ? r.pb_ratio.toFixed(2) : '—'}</td>
                    <td className="font-mono">{r.roe != null ? `${(r.roe * 100).toFixed(1)}%` : '—'}</td>
                    <td><RecommendationBadge recommendation={r.recommendation} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && results.length === 0 && total === 0 && (
          <div className="glass-card" style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
            Bir şablon seç veya filtre uygula, ardından &quot;Tara&quot; butonuna bas.
          </div>
        )}
      </TerminalShell>
    </AppShell>
  );
}
