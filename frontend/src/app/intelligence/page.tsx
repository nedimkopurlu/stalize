'use client';

import React, { useEffect, useRef, useState } from 'react';
import AppShell from '@/components/AppShell';
import api, { MarketFeedItem, KapNotification } from '@/lib/api';
import styles from './page.module.css';

// ── Types ──────────────────────────────────────────────────

type FilterTab = 'tumu' | 'kap' | 'piyasa' | 'makro' | 'resmi';

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

function isOfficialItem(entry: FeedEntry): boolean {
  return ['TCMB', 'TUIK', 'TÜİK', 'HMB', 'Borsa İstanbul', 'MKK', 'Takasbank'].includes(entry.publisher);
}

function isMakroItem(entry: FeedEntry): boolean {
  const cat = (entry.category ?? '').toLowerCase();
  return ['TCMB', 'TUIK', 'TÜİK', 'HMB'].includes(entry.publisher) || cat === 'macro' || cat === 'makro' || cat.includes('macro') || cat.includes('makro');
}

function isTurkeySource(entry: FeedEntry): boolean {
  const source = entry.publisher;
  const allowedSources = new Set([
    'KAP',
    'TCMB',
    'TUIK',
    'TÜİK',
    'HMB',
    'Borsa İstanbul',
    'MKK',
    'Takasbank',
    'Bloomberg HT',
    'Ekonomim',
    'Dünya',
    'Dunya',
    'CNBC-e',
    'Bigpara',
    'A Para',
    'Borsa Gündem',
    'Finans Gündem',
    'Para Analiz',
    'Mynet Finans',
    'Foreks',
    'Borsa Direkt',
    'InvestAZ',
  ]);
  const url = (entry.sourceUrl ?? '').toLowerCase();
  const allowedDomains = [
    'kap.org.tr',
    'tcmb.gov.tr',
    'tuik.gov.tr',
    'hmb.gov.tr',
    'borsaistanbul.com',
    'mkk.com.tr',
    'takasbank.com.tr',
    'bloomberght.com',
    'ekonomim.com',
    'dunya.com',
    'cnbce.com',
    'bigpara.hurriyet.com.tr',
    'apara.com.tr',
    'borsagundem.com.tr',
    'finansgundemi.com',
    'paraanaliz.com',
    'finans.mynet.com',
    'foreks.com',
    'borsadirekt.com',
    'investaz.com.tr',
    'news.google.com',
  ];
  return allowedSources.has(source) && allowedDomains.some((domain) => url.includes(domain));
}

function getDomain(url?: string | null): string {
  if (!url) return '';
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

function fromMarketFeedItem(item: MarketFeedItem, index: number): FeedEntry {
  return {
    id: `intel-${item.trigger_id}-${item.timestamp}-${index}`,
    headline: item.headline,
    summary: item.original_headline !== item.headline ? item.original_headline : undefined,
    publisher: item.publisher ?? '',
    symbol: item.symbol,
    category: item.category,
    timestamp: item.timestamp,
    sourceUrl: item.source_url,
    importanceScore: item.importance_score ?? (item.sentiment_score > 0.6 ? 0.75 : item.sentiment_score > 0.3 ? 0.5 : 0.2),
    type: 'intelligence',
  };
}

function fromKapNotification(item: KapNotification, index: number): FeedEntry {
  return {
    id: `kap-${item.id}-${item.published_at}-${index}`,
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

function NewsCard({ entry, expanded, onToggle, isNew = false }: {
  entry: FeedEntry;
  expanded: boolean;
  onToggle: () => void;
  isNew?: boolean;
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
          {isNew && (
            <span className={styles.newBadge}>Yeni</span>
          )}
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
                {getDomain(entry.sourceUrl) || 'Kaynak'}
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
  const [dailySummary, setDailySummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterTab>('tumu');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [newEntryIds, setNewEntryIds] = useState<Set<string>>(new Set());
  const loadingRef = useRef(false);
  const seenEntryIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    void loadData();
    const timer = window.setInterval(() => {
      void loadData({ silent: true });
    }, 10000);

    return () => window.clearInterval(timer);
  }, []);

  async function loadData(options?: { silent?: boolean }) {
    if (loadingRef.current) return;
    loadingRef.current = true;
    if (options?.silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const [overview, kapFeed] = await Promise.allSettled([
        api.getIntelligenceOverview(50),
        api.getKapFeed(20),
      ]);

      const intelligenceEntries: FeedEntry[] =
        overview.status === 'fulfilled'
          ? overview.value.feed.map(fromMarketFeedItem).filter((entry) => entry.sourceUrl && entry.publisher && isTurkeySource(entry))
          : [];

      const kapEntries: FeedEntry[] =
        kapFeed.status === 'fulfilled'
          ? kapFeed.value.map(fromKapNotification).filter((entry) => entry.sourceUrl && isTurkeySource(entry))
          : [];

      const seen = new Set<string>();
      const merged = [...intelligenceEntries, ...kapEntries].filter((entry) => {
        const key = `${entry.sourceUrl ?? ''}|${entry.headline}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      const previousIds = seenEntryIdsRef.current;
      const nextIds = new Set(merged.map((entry) => entry.id));
      const incomingIds = options?.silent
        ? new Set(merged.filter((entry) => !previousIds.has(entry.id)).map((entry) => entry.id))
        : new Set<string>();

      setEntries(merged);
      setNewEntryIds(incomingIds);
      setLastUpdated(new Date().toISOString());
      seenEntryIdsRef.current = nextIds;

      // Non-blocking — banner is optional; never blocks feed loading
      api.getDailySummary().then((r) => setDailySummary(r.summary)).catch(() => null);

      if (incomingIds.size > 0) {
        window.setTimeout(() => {
          setNewEntryIds(new Set());
        }, 8000);
      }

      if (intelligenceEntries.length === 0 && kapEntries.length === 0) {
        setError('Haber verisi alınamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Veriler alınamadı');
    } finally {
      setLoading(false);
      setRefreshing(false);
      loadingRef.current = false;
    }
  }

  const filtered = entries.filter((e) => {
    if (filter === 'tumu') return true;
    if (filter === 'kap') return isKapItem(e);
    if (filter === 'resmi') return isOfficialItem(e);
    if (filter === 'makro') return isMakroItem(e);
    if (filter === 'piyasa') return !isKapItem(e) && !isMakroItem(e);
    return true;
  });

  const FILTERS: { key: FilterTab; label: string }[] = [
    { key: 'tumu', label: 'Tümü' },
    { key: 'kap', label: 'KAP' },
    { key: 'piyasa', label: 'Piyasa' },
    { key: 'makro', label: 'Makro' },
    { key: 'resmi', label: 'Resmi' },
  ];

  const sourceCount = new Set(entries.map((entry) => entry.publisher)).size;
  const latestEntry = entries[0];

  return (
    <AppShell>
      <div className={styles.page}>
        {/* Header */}
        <div className={styles.pageHeader}>
          <div className={styles.headerLeft}>
            <p className={styles.eyebrow}>TÜRKİYE · TÜRKÇE KAYNAKLAR</p>
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

        <div className={styles.scopeRail}>
          <span>TR</span>
          <span>Türkçe</span>
          <span>{sourceCount > 0 ? `${sourceCount} kaynak` : 'Kaynak bekleniyor'}</span>
          <span>{latestEntry ? `Son: ${formatTime(latestEntry.timestamp)}` : 'Son veri yok'}</span>
          <span className={refreshing ? styles.liveRefreshing : styles.liveIdle}>
            {refreshing ? 'Yenileniyor' : lastUpdated ? `Canlı: ${formatTime(lastUpdated)}` : 'Canlı'}
          </span>
        </div>

        {/* ─── Günlük AI Piyasa Özeti ─── */}
        {dailySummary && (
          <div className={styles.aiSummaryBanner}>
            <span className={styles.aiSummaryIcon}>✦</span>
            <div className={styles.aiSummaryText}>
              <span className={styles.aiSummaryLabel}>Günlük Piyasa Özeti</span>
              <p className={styles.aiSummaryBody}>{dailySummary}</p>
            </div>
          </div>
        )}

        {/* Content */}
        {error && (
          <div className={styles.errorMsg}>{error}</div>
        )}

        {loading ? (
          <SkeletonCards />
        ) : filtered.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>📭</div>
            <div className={styles.emptyTitle}>Haber bulunamadı</div>
            <p className={styles.emptyDesc}>Bu filtreyle eşleşen haber bulunamadı. Filtre seçimini değiştirin.</p>
          </div>
        ) : (
          <div className={styles.feedList}>
            {filtered.map((entry) => (
              <NewsCard
                key={entry.id}
                entry={entry}
                expanded={expandedId === entry.id}
                onToggle={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                isNew={newEntryIds.has(entry.id)}
              />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
