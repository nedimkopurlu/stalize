'use client';

import { useEffect, useMemo, useState } from 'react';
import AppShell from '@/components/AppShell';
import api, { DiagnosticItem, SystemDiagnosticsResponse } from '@/lib/api';
import styles from './page.module.css';

const STATUS_LABELS = {
  ok: 'Çalışıyor',
  warning: 'Uyarı',
  critical: 'Arıza',
} as const;

function statusClass(status: DiagnosticItem['status']) {
  if (status === 'critical') return styles.critical;
  if (status === 'warning') return styles.warning;
  return styles.ok;
}

function overallLabel(status: SystemDiagnosticsResponse['status']) {
  if (status === 'down') return 'Kritik arıza var';
  if (status === 'degraded') return 'Dikkat isteyen sistemler var';
  return 'Tüm ana sistemler çalışıyor';
}

function MetadataView({ metadata }: { metadata: Record<string, unknown> }) {
  const text = JSON.stringify(metadata, null, 2);
  if (!metadata || text === '{}') return null;
  return <pre className={styles.metadata}>{text}</pre>;
}

export default function ErrorsPage() {
  const [data, setData] = useState<SystemDiagnosticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | DiagnosticItem['status']>('all');

  async function loadDiagnostics() {
    setError(null);
    try {
      const res = await api.getSystemDiagnostics();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Diagnostik raporu alınamadı');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDiagnostics();
  }, []);

  const filteredItems = useMemo(() => {
    const items = data?.items ?? [];
    if (filter === 'all') return items;
    return items.filter((item) => item.status === filter);
  }, [data, filter]);

  return (
    <AppShell>
      <main className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Gizli sistem arıza paneli</p>
            <h1 className={styles.title}>Sistem Durum Tespiti</h1>
          </div>
          <button type="button" className={styles.refreshButton} onClick={() => void loadDiagnostics()}>
            Yenile
          </button>
        </header>

        <section className={`${styles.overview} ${data ? styles[`overall_${data.status}`] : ''}`}>
          <div>
            <span className={styles.overviewLabel}>Genel Durum</span>
            <strong>{data ? overallLabel(data.status) : loading ? 'Kontrol ediliyor' : 'Rapor yok'}</strong>
          </div>
          <div className={styles.counters}>
            <span><b>{data?.summary.critical ?? 0}</b> arıza</span>
            <span><b>{data?.summary.warning ?? 0}</b> uyarı</span>
            <span><b>{data?.summary.ok ?? 0}</b> sağlam</span>
          </div>
        </section>

        <section className={styles.filterBar}>
          {(['all', 'critical', 'warning', 'ok'] as const).map((item) => (
            <button
              key={item}
              type="button"
              className={`${styles.filterButton} ${filter === item ? styles.filterActive : ''}`}
              onClick={() => setFilter(item)}
            >
              {item === 'all' ? 'Tümü' : STATUS_LABELS[item]}
            </button>
          ))}
        </section>

        {error && <div className={styles.error}>{error}</div>}

        <section className={styles.grid}>
          {loading ? (
            Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className={styles.skeleton} />
            ))
          ) : filteredItems.length === 0 ? (
            <div className={styles.empty}>Bu filtrede kayıt yok.</div>
          ) : (
            filteredItems.map((item) => (
              <article key={item.key} className={`${styles.card} ${statusClass(item.status)}`}>
                <div className={styles.cardTop}>
                  <div>
                    <span className={styles.key}>{item.key}</span>
                    <h2>{item.title}</h2>
                  </div>
                  <span className={styles.statusBadge}>{STATUS_LABELS[item.status]}</span>
                </div>
                <p className={styles.detail}>{item.detail}</p>
                <div className={styles.fixBox}>
                  <span>Çözüm</span>
                  <p>{item.remediation}</p>
                </div>
                <MetadataView metadata={item.metadata} />
              </article>
            ))
          )}
        </section>
      </main>
    </AppShell>
  );
}
