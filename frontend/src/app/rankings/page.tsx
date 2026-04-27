'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import ScoreRing from '@/components/ScoreRing';
import RecommendationBadge, { PriceChange, formatPrice } from '@/components/StockHelpers';
import { TerminalEmpty, TerminalPageHeader, TerminalSection, TerminalShell } from '@/components/TerminalPrimitives';
import api, { StockSummary } from '@/lib/api';
import styles from './rankings.module.css';

export default function RankingsPage() {
  const [bist100Rankings, setBist100Rankings] = useState<StockSummary[]>([]);
  const [bestTechnical, setBestTechnical] = useState<StockSummary[]>([]);
  const [bestFundamental, setBestFundamental] = useState<StockSummary[]>([]);
  const [bestMomentum, setBestMomentum] = useState<StockSummary[]>([]);
  const [bestNews, setBestNews] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadRankings();
  }, []);

  async function loadRankings() {
    setLoading(true);
    try {
      const [all, tech, fund, news, momentum] = await Promise.all([
        api.getRankings({ sort_by: 'overall_score', limit: 30 }),
        api.getRankings({ sort_by: 'technical_score', limit: 10 }),
        api.getRankings({ sort_by: 'fundamental_score', limit: 10 }),
        api.getRankings({ sort_by: 'sentiment_score', limit: 10 }),
        api.getRankings({ sort_by: 'daily_change_pct', limit: 10 }),
      ]);
      setBist100Rankings(all.rankings);
      setBestTechnical(tech.rankings);
      setBestFundamental(fund.rankings);
      setBestNews(news.rankings);
      setBestMomentum(momentum.rankings);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
        <TerminalShell>
          <TerminalPageHeader
            title="Sıralama"
            description="Genel skor, teknik kalite, temel sağlamlık ve haber etkisini aynı tabloda karşılaştır."
            action={(
              <button className="btn btn-primary" onClick={loadRankings} disabled={loading}>
                {loading ? 'Yükleniyor...' : 'Sıralamayı Yenile'}
              </button>
            )}
          />
          <TerminalSection
            title="Genel Sıralama"
            description="Portföy ve radar ekranlarıyla aynı skor mantığını kullanan ana liderlik tablosu."
          >
            {loading ? (
              <TerminalEmpty>Sıralama hesaplanıyor...</TerminalEmpty>
            ) : (
              <div className={styles.tableWrap}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Hisse</th>
                      <th>Fiyat</th>
                      <th>Genel</th>
                      <th className="hide-mobile">Teknik</th>
                      <th className="hide-mobile">Temel</th>
                      <th className="hide-mobile">Haber</th>
                      <th>Sinyal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bist100Rankings.map((stock, index) => (
                      <tr key={stock.symbol}>
                        <td className="font-mono" style={{ color: index < 3 ? 'var(--accent-cyan)' : 'var(--text-muted)', fontWeight: 800 }}>
                          {index + 1}
                        </td>
                        <td>
                          <Link href={`/stocks/${stock.symbol}`} style={{ color: 'inherit', textDecoration: 'none', fontWeight: 800 }}>
                            {stock.symbol}
                          </Link>
                        </td>
                        <td className="font-mono">{formatPrice(stock.current_price)}</td>
                        <td><ScoreRing score={stock.overall_score} size={40} strokeWidth={4} /></td>
                        <td className="hide-mobile"><ScoreRing score={stock.technical_score} size={30} strokeWidth={2} /></td>
                        <td className="hide-mobile"><ScoreRing score={stock.fundamental_score} size={30} strokeWidth={2} /></td>
                        <td className="hide-mobile"><ScoreRing score={stock.sentiment_score} size={30} strokeWidth={2} /></td>
                        <td><RecommendationBadge recommendation={stock.recommendation} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </TerminalSection>

          <div className={styles.miniGrid}>
            <MiniRankCard title="En İyi Teknik" stocks={bestTechnical} metric="technical_score" />
            <MiniRankCard title="En Güçlü Temel" stocks={bestFundamental} metric="fundamental_score" />
            <MiniRankCard title="Haber Etkisi" stocks={bestNews} metric="sentiment_score" />
            <MiniRankCard title="Günlük Momentum" stocks={bestMomentum} metric="daily_change_pct" />
          </div>
        </TerminalShell>
    </AppShell>
  );
}

type RankingMetric = 'technical_score' | 'fundamental_score' | 'sentiment_score' | 'daily_change_pct';

function MiniRankCard({ title, stocks, metric }: { title: string; stocks: StockSummary[]; metric: RankingMetric }) {
  return (
    <TerminalSection title={title} description="Alt kırılım liderleri" muted>
      {stocks.length === 0 ? (
        <TerminalEmpty>Henüz veri yok.</TerminalEmpty>
      ) : (
        <div className={styles.miniList}>
          {stocks.map((stock, index) => (
            <Link key={stock.symbol} href={`/stocks/${stock.symbol}`} className={styles.miniItem}>
              <div className={styles.miniMeta}>
                <span className={styles.miniRank}>{index + 1}</span>
                <span className={styles.miniSymbol}>{stock.symbol}</span>
              </div>
              {metric === 'daily_change_pct' ? (
                <PriceChange value={stock.daily_change_pct} />
              ) : (
                <span className={styles.miniValue}>{(stock[metric] ?? 0).toFixed(1)}</span>
              )}
            </Link>
          ))}
        </div>
      )}
    </TerminalSection>
  );
}
