'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { safeLabel, safeLabelTooltip } from '@/components/StockHelpers';
import api, {
  ModelPortfolioCurrentResponse,
  ModelPortfolioHistoryResponse,
  ModelPortfolioHolding,
  PortfolioHistoryResponse,
} from '@/lib/api';
import styles from './page.module.css';

function formatPct(value: number | null | undefined, digits = 1, showPlus = true): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-';
  const sign = value > 0 && showPlus ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-';
  return value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' });
}

function toneClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return styles.neutral;
  return value >= 0 ? styles.positive : styles.negative;
}

function score(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return Math.round(value).toString();
}

function safeColor(rec: string | null): string {
  if (!rec) return 'var(--text-muted)';
  if (rec === 'GÜÇLÜ AL' || rec === 'AL') return 'var(--accent-green)';
  if (rec === 'GÜÇLÜ SAT' || rec === 'SAT') return 'var(--accent-red)';
  return 'var(--accent)';
}

function HoldingRow({ holding }: { holding: ModelPortfolioHolding }) {
  return (
    <Link href={`/stocks/${holding.symbol}`} className={styles.holdingRow}>
      <div className={styles.symbolCell}>
        <strong>{holding.symbol}</strong>
        <span>{holding.name ?? holding.sector ?? '-'}</span>
      </div>
      <span>{holding.sector ?? '-'}</span>
      <strong>{formatPct(holding.allocation_pct, 1, false)}</strong>
      <span>{formatPrice(holding.current_price)}</span>
      <strong className={toneClass(holding.weekly_return_pct)}>{formatPct(holding.weekly_return_pct)}</strong>
      <span
        title={safeLabelTooltip(holding.recommendation)}
        style={{ fontSize: '0.78rem', color: safeColor(holding.recommendation) }}
      >
        {safeLabel(holding.recommendation)}
      </span>
      <div className={styles.scoreStack}>
        <span>Genel {score(holding.overall_score)}</span>
        <span>Teknik {score(holding.technical_score)}</span>
        <span>Temel {score(holding.fundamental_score)}</span>
      </div>
      <p>{holding.rationale ?? 'Model bu hisseyi skor, sektör dengesi ve fiyat davranışı nedeniyle listede tutuyor.'}</p>
    </Link>
  );
}

export default function ModelPortfolioPage() {
  const [current, setCurrent] = useState<ModelPortfolioCurrentResponse | null>(null);
  const [history, setHistory] = useState<ModelPortfolioHistoryResponse | null>(null);
  const [userHistory, setUserHistory] = useState<PortfolioHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      const [currentResult, historyResult, userHistoryResult] = await Promise.allSettled([
        api.getCurrentModelPortfolio(),
        api.getModelPortfolioHistory(10),
        api.getPortfolioHistory(30),
      ]);
      if (cancelled) return;

      if (currentResult.status === 'fulfilled') {
        setCurrent(currentResult.value);
      } else {
        setError(currentResult.reason instanceof Error ? currentResult.reason.message : 'Model portföy alınamadı');
      }
      if (historyResult.status === 'fulfilled') setHistory(historyResult.value);
      if (userHistoryResult.status === 'fulfilled') setUserHistory(userHistoryResult.value);
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const holdings = useMemo(() => current?.holdings ?? [], [current]);
  const week = current?.week ?? null;
  const decision = current?.decision_band ?? null;
  const changes = current?.changes ?? null;
  const reviewNotes = week?.review_notes ?? null;
  const userReturn = userHistory?.risk_summary.latest_portfolio_return_pct ?? null;

  const sectorWeights = useMemo(() => {
    const map = holdings.reduce<Record<string, number>>((acc, holding) => {
      const sector = holding.sector ?? 'Bilinmeyen';
      acc[sector] = (acc[sector] ?? 0) + holding.allocation_pct;
      return acc;
    }, {});
    return Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [holdings]);

  const totalAllocation = holdings.reduce((sum, holding) => sum + holding.allocation_pct, 0);
  const bestHolding = current?.summary?.best_holding;
  const worstHolding = current?.summary?.worst_holding;

  return (
    <AppShell>
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <span className={styles.eyebrow}>Model Portföy</span>
            <h1>Haftanın seçilmiş BIST portföyü</h1>
            <p>
              {decision?.headline || week?.review_summary || 'Model portföy hazırlanıyor. Uygun hisseler skor, sektör dengesi ve risk kontrolüyle seçilecek.'}
            </p>
            <div className={styles.heroFacts}>
              <div>
                <span>Model getiri</span>
                <strong className={toneClass(week?.portfolio_return_pct)}>{formatPct(week?.portfolio_return_pct)}</strong>
              </div>
              <div>
                <span>BIST100</span>
                <strong className={toneClass(week?.benchmark_return_pct)}>{formatPct(week?.benchmark_return_pct)}</strong>
              </div>
              <div>
                <span>Aktif fark</span>
                <strong className={toneClass(week?.active_return_spread)}>{formatPct(week?.active_return_spread)}</strong>
              </div>
            </div>
          </div>

          <aside className={styles.sideCard}>
            <span className={styles.eyebrow}>Karar bandı</span>
            <strong>{decision?.focus || 'Dengeli takip'}</strong>
            <p>{week ? `${formatDate(week.week_start)} - ${formatDate(week.week_end)}` : 'Hafta verisi bekleniyor'}</p>
            <div className={styles.sideRows}>
              <div>
                <span>Pozisyon</span>
                <strong>{holdings.length || '-'}</strong>
              </div>
              <div>
                <span>Portföyüm</span>
                <strong className={toneClass(userReturn)}>{formatPct(userReturn)}</strong>
              </div>
              <div>
                <span>Ağırlık</span>
                <strong>{totalAllocation.toFixed(0)}%</strong>
              </div>
            </div>
          </aside>
        </section>

        {error && <div className={styles.errorMsg}>{error}</div>}

        {loading ? (
          <section className={styles.loadingPanel}>
            <span />
            <span />
            <span />
          </section>
        ) : holdings.length === 0 ? (
          <section className={styles.emptyPanel}>
            <strong>Model portföy henüz oluşmadı</strong>
            <p>Skorlar ve fiyat verileri hazır olduğunda haftalık portföy burada görünecek.</p>
          </section>
        ) : (
          <>
            <section className={styles.holdingsPanel}>
              <div className={styles.panelHeader}>
                <div>
                  <span className={styles.eyebrow}>Hisseler</span>
                  <h2>Modelin aldığı hisseler</h2>
                </div>
                <span>{holdings.length} hisse</span>
              </div>

              <div className={styles.tableHeader}>
                <span>Hisse</span>
                <span>Sektör</span>
                <span>Ağırlık</span>
                <span>Fiyat</span>
                <span>Hafta</span>
                <span>Karar</span>
                <span>Skorlar</span>
                <span>Gerekçe</span>
              </div>
              <div className={styles.holdingList}>
                {holdings.map((holding) => (
                  <HoldingRow key={`${holding.id}-${holding.symbol}`} holding={holding} />
                ))}
              </div>
            </section>

            <section className={styles.analysisGrid}>
              <article className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <span className={styles.eyebrow}>AI Denetçi</span>
                    <h2>Neyi neden tutuyor?</h2>
                  </div>
                </div>
                <p className={styles.reviewText}>
                  {week?.review_summary || 'AI denetçi bu hafta için ek gerekçe üretmedi; deterministik skor ve risk dağılımı geçerli.'}
                </p>
                {decision?.actions?.length ? (
                  <div className={styles.actionList}>
                    {decision.actions.map((action) => <span key={action}>{action}</span>)}
                  </div>
                ) : null}
              </article>

              <article className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <span className={styles.eyebrow}>Risk ve Dağılım</span>
                    <h2>Sektör ağırlığı</h2>
                  </div>
                </div>
                <div className={styles.sectorList}>
                  {sectorWeights.map(([sector, allocation]) => (
                    <div key={sector} className={styles.sectorRow}>
                      <div>
                        <span>{sector}</span>
                        <strong>{formatPct(allocation, 1, false)}</strong>
                      </div>
                      <div className={styles.barTrack}>
                        <span style={{ width: `${Math.min(100, allocation)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
                {reviewNotes?.weakest_dimension && (
                  <p className={styles.smallNote}>Zayıf halka: {reviewNotes.weakest_dimension}</p>
                )}
              </article>
            </section>

            <section className={styles.analysisGrid}>
              <article className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <span className={styles.eyebrow}>Performans</span>
                    <h2>En iyi ve en zayıf</h2>
                  </div>
                </div>
                <div className={styles.extremeGrid}>
                  <div>
                    <span>En iyi</span>
                    <strong>{bestHolding?.symbol ?? '-'}</strong>
                    <b className={toneClass(bestHolding?.weekly_return_pct)}>{formatPct(bestHolding?.weekly_return_pct)}</b>
                  </div>
                  <div>
                    <span>En zayıf</span>
                    <strong>{worstHolding?.symbol ?? '-'}</strong>
                    <b className={toneClass(worstHolding?.weekly_return_pct)}>{formatPct(worstHolding?.weekly_return_pct)}</b>
                  </div>
                </div>
              </article>

              <article className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <span className={styles.eyebrow}>Değişiklikler</span>
                    <h2>Bu hafta ne değişti?</h2>
                  </div>
                </div>
                <p className={styles.reviewText}>{changes?.summary || 'Önceki haftaya göre karşılaştırma verisi bekleniyor.'}</p>
                {changes && (
                  <div className={styles.changeChips}>
                    {changes.added.slice(0, 4).map((symbol) => <span key={`a-${symbol}`}>Eklendi {symbol}</span>)}
                    {changes.removed.slice(0, 4).map((symbol) => <span key={`r-${symbol}`}>Çıktı {symbol}</span>)}
                  </div>
                )}
              </article>
            </section>

            <section className={styles.historyPanel}>
              <div className={styles.panelHeader}>
                <div>
                  <span className={styles.eyebrow}>Geçmiş</span>
                  <h2>Haftalık model performansı</h2>
                </div>
                <span>{history?.count ?? 0} hafta</span>
              </div>

              <div className={styles.historyList}>
                {(history?.weeks ?? []).map((item) => (
                  <div key={item.id} className={styles.historyRow}>
                    <span>{formatDate(item.week_start)} - {formatDate(item.week_end)}</span>
                    <strong className={toneClass(item.portfolio_return_pct)}>{formatPct(item.portfolio_return_pct)}</strong>
                    <span>BIST100 {formatPct(item.benchmark_return_pct)}</span>
                    <span className={toneClass(item.active_return_spread)}>Fark {formatPct(item.active_return_spread)}</span>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </AppShell>
  );
}
