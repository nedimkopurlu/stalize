'use client';
import React, { useState, useEffect, useCallback } from 'react';
import AppShell from '@/components/AppShell';
import { TerminalPageHeader, TerminalShell, TerminalEmpty } from '@/components/TerminalPrimitives';
import RecommendationBadge, { PriceChange, formatPrice } from '@/components/StockHelpers';
import ScoreRing from '@/components/ScoreRing';
import api, { StockSummary } from '@/lib/api';
import Link from 'next/link';

const STORAGE_KEY = 'stalize-watchlist';

function loadWatchlist(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as string[];
  } catch {
    return [];
  }
}

function saveWatchlist(symbols: string[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols));
}

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [addInput, setAddInput] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setSymbols(loadWatchlist());
  }, []);

  const fetchStocks = useCallback(async (syms: string[]) => {
    if (syms.length === 0) { setStocks([]); return; }
    setLoading(true);
    try {
      // Sadece izleme listesindeki sembolleri çek — 500 hisse değil
      const res = await api.getStocks({ symbols: syms.join(','), sort_by: 'overall_score', limit: syms.length + 5 });
      const watchlistStocks = res.stocks;
      // İzleme listesi sırasını koru
      const ordered = syms.map(sym => watchlistStocks.find(s => s.symbol === sym)).filter(Boolean) as StockSummary[];
      setStocks(ordered);
      setError('');
    } catch (err) {
      setStocks([]);
      setError(err instanceof Error ? err.message : 'İzleme listesi verileri alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStocks(symbols);
  }, [symbols, fetchStocks]);

  function addSymbol() {
    const sym = addInput.trim().toUpperCase();
    if (!sym) return;
    if (symbols.includes(sym)) { setError(`${sym} zaten listede`); return; }
    const newSymbols = [...symbols, sym];
    setSymbols(newSymbols);
    saveWatchlist(newSymbols);
    setAddInput('');
    setError('');
  }

  function removeSymbol(sym: string) {
    if (!window.confirm(`${sym} izleme listesinden çıkarılsın mı?`)) return;
    const newSymbols = symbols.filter(s => s !== sym);
    setSymbols(newSymbols);
    saveWatchlist(newSymbols);
  }

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="İzleme Listesi"
          description="Takip etmek istediğin hisseleri buraya ekle — fiyat, skor ve sinyal tek bakışta."
          action={
            <button className="btn btn-primary" onClick={() => void fetchStocks(symbols)}>
              Yenile
            </button>
          }
        />

        {/* Add symbol */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
          <input
            className="search-input"
            placeholder="Hisse sembolü ekle (örn: AKBNK)"
            value={addInput}
            onChange={e => { setAddInput(e.target.value.toUpperCase()); setError(''); }}
            onKeyDown={e => { if (e.key === 'Enter') addSymbol(); }}
            style={{ maxWidth: 260 }}
          />
          <button className="btn btn-primary btn-sm" onClick={addSymbol}>Ekle</button>
          {error && <span style={{ color: 'var(--red-500)', fontSize: '0.82rem' }}>{error}</span>}
        </div>

        {error && (
          <div className="glass-card" style={{ marginBottom: 16, color: 'var(--red-500)' }}>
            {error}
          </div>
        )}

        {symbols.length === 0 ? (
          <TerminalEmpty>
            İzleme listesi boş. Hisse sembolü girerek başla.
          </TerminalEmpty>
        ) : (
          <div className="glass-card" style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Hisse</th>
                  <th>Fiyat</th>
                  <th>Değişim</th>
                  <th>Sektör</th>
                  <th>Skor</th>
                  <th>Sinyal</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: symbols.length }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={7}><div className="skeleton" style={{ height: 20, width: '100%' }} /></td>
                    </tr>
                  ))
                ) : (
                  stocks.map(s => (
                    <tr key={s.symbol}>
                      <td>
                        <Link href={`/stocks/${s.symbol}`} style={{ color: 'var(--accent-cyan)', fontWeight: 600, textDecoration: 'none' }}>
                          {s.symbol}
                        </Link>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.name?.substring(0, 22)}</div>
                      </td>
                      <td className="font-mono">{formatPrice(s.current_price)}</td>
                      <td><PriceChange value={s.daily_change_pct} /></td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{s.sector || '—'}</td>
                      <td><ScoreRing score={s.overall_score} size={36} strokeWidth={3} /></td>
                      <td><RecommendationBadge recommendation={s.recommendation} /></td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => removeSymbol(s.symbol)}
                          style={{ color: 'var(--red-500)', fontSize: '0.75rem' }}
                        >
                          Çıkar
                        </button>
                      </td>
                    </tr>
                  ))
                )}
                {!loading && stocks.length < symbols.length && (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      {symbols.length - stocks.length} hisse verisi bulunamadı
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </TerminalShell>
    </AppShell>
  );
}
