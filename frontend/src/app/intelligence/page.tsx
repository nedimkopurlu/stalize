'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { TerminalEmpty, TerminalError, TerminalPageHeader, TerminalSection, TerminalShell } from '@/components/TerminalPrimitives';
import api, { IntelligenceOverview } from '@/lib/api';
import styles from './intelligence.module.css';

export default function IntelligencePage() {
  const [data, setData] = useState<IntelligenceOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadOverview();
  }, []);

  async function loadOverview() {
    setLoading(true);
    setError(null);
    try {
      const overview = await api.getIntelligenceOverview(12);
      setData(overview);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Intelligence verisi alınamadı');
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
        <TerminalShell>
          <TerminalPageHeader
            title="Piyasa Akışı"
            description="KAP, resmi kaynaklar ve yüksek etkili haberleri tek akışta izle."
            action={(
              <button className="btn btn-primary" onClick={loadOverview} disabled={loading}>
                {loading ? 'Yükleniyor...' : 'Akışı Yenile'}
              </button>
            )}
          />
          {error && (
            <TerminalError>{error}</TerminalError>
          )}

          {loading && !data ? (
            <TerminalSection title="Akış Hazırlanıyor" description="Kaynaklar toplanıyor">
              <TerminalEmpty>Intelligence akışı hazırlanıyor...</TerminalEmpty>
            </TerminalSection>
          ) : data ? (
            <>
            <div className={styles.mainGrid}>
              <div className="card">
                <div className={styles.panelHeader}>
                  <div>
                    <h2 className={styles.sectionTitle}>Canlı Intelligence Akışı</h2>
                    <p className={styles.panelSub}>KAP ve yüksek etkili haberler tek terminalde</p>
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={loadOverview}>
                    Yenile
                  </button>
                </div>

                <div className={styles.feedList}>
                  {data.feed.map((item, index) => (
                    <a
                      key={`${item.trigger_id}-${index}`}
                      href={item.source_url ?? '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.feedItem}
                    >
                      <div className={styles.feedMeta}>
                        <span className={styles.feedSource}>{item.publisher ?? 'Kaynak'}</span>
                        <span className={styles.feedTime}>
                          {new Date(item.timestamp).toLocaleString('tr-TR', {
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <div className={styles.feedHeadline}>{item.headline}</div>
                      <div className={styles.feedFoot}>
                        <span>{item.symbol ?? item.trigger_id.toUpperCase()}</span>
                        <span className={item.sentiment_score >= 0 ? styles.signalUp : styles.signalDown}>
                          {item.sentiment_score >= 0 ? 'Pozitif akış' : 'Negatif akış'}
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div className="card">
                  <div className={styles.panelHeader}>
                    <div>
                      <h2 className={styles.sectionTitle}>Kaynak Gücü</h2>
                      <p className={styles.panelSub}>Birleşik akıştaki dağılım</p>
                    </div>
                  </div>
                  <div className={styles.sourceList}>
                    {Object.entries(data.source_summary)
                      .sort(([, a], [, b]) => b - a)
                      .map(([source, count]) => (
                        <div key={source} className={styles.sourceItem}>
                          <div>
                            <div className={styles.sourceName}>{source}</div>
                            <div className={styles.sourceBar}>
                              <div
                                className={styles.sourceFill}
                                style={{ width: `${Math.min(100, (count / Math.max(...Object.values(data.source_summary))) * 100)}%` }}
                              />
                            </div>
                          </div>
                          <div className={styles.sourceCount}>{count}</div>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="card">
                  <div className={styles.panelHeader}>
                    <div>
                      <h2 className={styles.sectionTitle}>Öne Çıkan Senaryolar</h2>
                      <p className={styles.panelSub}>Etki skoruna göre en güçlü birleşik olaylar</p>
                    </div>
                  </div>
                  <div className={styles.scenarioList}>
                    {data.scenarios.length === 0 && (
                      <div className={styles.emptyState}>Henüz senaryo üretilmedi.</div>
                    )}
                    {data.scenarios.map((scenario, index) => (
                      <div key={`${scenario.scenario.trigger_id}-${index}`} className={styles.scenarioItem}>
                        <div className={styles.scenarioMeta}>
                          <span className={styles.scenarioSource}>{scenario.scenario.publisher ?? 'Kaynak'}</span>
                          <span className={styles.scenarioTime}>{scenario.summary.total_stocks_affected} hisse</span>
                        </div>
                        <div className={styles.scenarioHeadline}>{scenario.summary.headline}</div>
                        <div className={styles.impactList}>
                          {scenario.impacts.slice(0, 3).map((impact) => (
                            <div key={`${scenario.scenario.trigger_id}-${impact.symbol}`} className={styles.impactItem}>
                              <span className={styles.impactSymbol}>{impact.symbol}</span>
                              <span className={styles.impactReason}>{impact.reasons[0] ?? 'Etki hesaplandı'}</span>
                              <span className={`${styles.impactScore} ${impact.impact_score >= 0 ? styles.signalUp : styles.signalDown}`}>
                                {impact.impact_score >= 0 ? '+' : ''}{impact.impact_score.toFixed(1)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            </>
          ) : null}
        </TerminalShell>
    </AppShell>
  );
}
