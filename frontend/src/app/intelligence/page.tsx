'use client';

import React, { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import api, { MarketFeedItem, KapNotification } from '@/lib/api';
import styles from './page.module.css';

// ── Types ──────────────────────────────────────────────────

type FilterTab = 'tumu' | 'kap' | 'haberler' | 'makro';

type ImpactLevel = 'high' | 'medium' | 'low';

interface FeedEntry {
  id: string;
  headline: string;
  summary?: string;
  publisher: string;
  symbol?: string;
  category?: string;
  timestamp: string;
  sourceUrl?: string | null;
  importanceScore: number;
  type: 'intelligence' | 'kap';
}

// ── Helpers ────────────────────────────────────────────────

function getImpact(score: number): ImpactLevel {
  if (score > 0.7) return 'high';
  if (score > 0.4) return 'medium';
  return 'low';
}

function impactLabel(level: ImpactLevel): string {
  if (level === 'high') return 'Yüksek Etki';
  if (level === 'medium') return 'Orta Etki';
  return 'Düşük Etki';
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Az önce';
    if (diffMin < 60) return `${diffMin}dk önce`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}s önce`;
    return d.toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function isKapItem(entry: FeedEntry): boolean {
  return entry.type === 'kap' || entry.publisher?.toUpperCase() === 'KAP';
}

function isMakroItem(entry: FeedEntry): boolean {
  const cat = (entry.category ?? '').toLowerCase();
  return cat === 'macro' || cat === 'makro' || cat.includes('macro') || cat.includes('makro');
}

function fromMarketFeedItem(item: MarketFeedItem): FeedEntry {
  return {
    id: item.trigger_id,
    headline: item.headline,
    summary: item.original_headline !== item.headline ? item.original_headline : undefined,
    publisher: item.publisher ?? 'Kaynak',
    symbol: item.symbol,
    category: item.category,
    timestamp: item.timestamp,
    sourceUrl: item.source_url,
    importanceScore: item.importance_score ?? (item.sentiment_score > 0.6 ? 0.75 : item.sentiment_score > 0.3 ? 0.5 : 0.2),
    type: 'intelligence',
  };
}

function fromKapNotification(item: KapNotification): FeedEntry {
  return {
    id: `kap-${item.id}`,
    headline: item.title,
    publisher: 'KAP',
    symbol: item.symbol,
    timestamp: item.published_at,
    sourceUrl: item.kap_url,
    importanceScore: 0.6,
    type: 'kap',
  };
}

// ── Skeleton ───────────────────────────────────────────────

function SkeletonCards() {
  return (
    <div className={styles.feedList}>
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className={styles.skeletonCard}>
          <div className={styles.skeletonBar} />
          <div className={styles.skeletonBody}>
            <div className={styles.skeletonMeta} />
            <div className={styles.skeletonTitle} style={{ width: i % 2 === 0 ? '85%' : '72%' }} />
            <div className={styles.skeletonSub} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── News Card ──────────────────────────────────────────────

function NewsCard({ entry, expanded, onToggle }: {
  entry: FeedEntry;
  expanded: boolean;
  onToggle: () => void;
}) {
  const impact = getImpact(entry.importanceScore);
  const label = impactLabel(impact);

  return (
    <div
      className={`${styles.card} ${expanded ? styles.cardExpanded : ''}`}
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggle(); }}
    >
      <div className={`${styles.impactBar} ${styles[`impactBar_${impact}`]}`} />

      <div className={styles.cardBody}>
        <div className={styles.metaRow}>
          <span className={styles.publisher}>{entry.publisher}</span>
          {entry.symbol && (
            <span className={styles.symbolTag}>{entry.symbol}</span>
          )}
          <span className={styles.metaDot}>·</span>
          <span className={styles.timeStamp}>{formatTime(entry.timestamp)}</span>
          <div className={styles.spacer} />
          <span className={`${styles.impactBadge} ${styles[`impactBadge_${impact}`]}`}>{label}</span>
        </div>

        <div className={styles.headline}>{entry.headline}</div>

        {entry.summary && !expanded && (
          <div className={styles.summary}>{entry.summary}</div>
        )}

        {expanded && (
          <div className={styles.expandedContent}>
            {entry.summary && (
              <div className={styles.expandedSummary}>{entry.summary}</div>
            )}
            {entry.sourceUrl && (
              <a
                href={entry.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.sourceLink}
                onClick={(e) => e.stopPropagation()}
              >
                Kaynağa git →
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────

export default function IntelligencePage() {
  const [entries, setEntries] = useState<FeedEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterTab>('tumu');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [overview, kapFeed] = await Promise.allSettled([
        api.getIntelligenceOverview(50),
        api.getKapFeed(20),
      ]);

      const intelligenceEntries: FeedEntry[] =
        overview.status === 'fulfilled'
          ? overview.value.feed.map(fromMarketFeedItem)
          : [];

      const kapEntries: FeedEntry[] =
        kapFeed.status === 'fulfilled'
          ? kapFeed.value.map(fromKapNotification)
          : [];

      // Merge and deduplicate by id, sort newest first
      const merged = [...intelligenceEntries, ...kapEntries];
      merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      setEntries(merged);

      if (intelligenceEntries.length === 0 && kapEntries.length === 0) {
        setError('Haber verisi alınamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Veriler alınamadı');
    } finally {
      setLoading(false);
    }
  }

  const filtered = entries.filter((e) => {
    if (filter === 'tumu') return true;
    if (filter === 'kap') return isKapItem(e);
    if (filter === 'makro') return isMakroItem(e);
    if (filter === 'haberler') return !isKapItem(e) && !isMakroItem(e);
    return true;
  });

  const FILTERS: { key: FilterTab; label: string }[] = [
    { key: 'tumu', label: 'Tümü' },
    { key: 'kap', label: 'KAP' },
    { key: 'haberler', label: 'Haberler' },
    { key: 'makro', label: 'Makro' },
  ];

  return (
    <AppShell>
      <div className={styles.page}>
        {/* Header */}
        <div className={styles.pageHeader}>
          <div className={styles.headerLeft}>
            <p className={styles.eyebrow}>KAP · PİYASA HABERLERİ</p>
            <h1 className={styles.pageTitle}>Haberler</h1>
          </div>
          <div className={styles.filterPills}>
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                className={`${styles.pill} ${filter === key ? styles.pillActive : ''}`}
                onClick={() => setFilter(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {error && (
          <div className={styles.errorMsg}>{error}</div>
        )}

        {loading ? (
          <SkeletonCards />
        ) : filtered.length === 0 ? (
          <div className={styles.emptyState}>Bu filtrede haber bulunamadı.</div>
        ) : (
          <div className={styles.feedList}>
            {filtered.map((entry) => (
              <NewsCard
                key={entry.id}
                entry={entry}
                expanded={expandedId === entry.id}
                onToggle={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
              />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
