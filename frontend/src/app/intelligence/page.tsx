'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import AppShell from '@/components/AppShell';
import api, { KapNotification, MarketFeedItem } from '@/lib/api';
import styles from './page.module.css';

type FilterTab = 'tumu' | 'kap' | 'piyasa' | 'makro' | 'resmi';
type ImpactLevel = 'high' | 'medium' | 'low';

interface AiAssessment {
  stance?: string;
  label?: string;
  action?: string;
  reasoning?: string;
  risk?: string;
  confidence?: number;
}

interface FeedEntry {
  id: string;
  headline: string;
  summary?: string;
  aiSummary?: string;
  aiAssessment?: AiAssessment | null;
  publisher: string;
  symbol?: string;
  category?: string;
  timestamp: string;
  sourceUrl?: string | null;
  importanceScore: number;
  type: 'intelligence' | 'kap';
}

const FILTERS: { key: FilterTab; label: string }[] = [
  { key: 'tumu', label: 'Tümü' },
  { key: 'kap', label: 'KAP' },
  { key: 'piyasa', label: 'Piyasa' },
  { key: 'makro', label: 'Makro' },
  { key: 'resmi', label: 'Resmi' },
];

function getImpact(score: number): ImpactLevel {
  if (score >= 0.75) return 'high';
  if (score >= 0.48) return 'medium';
  return 'low';
}

function impactLabel(level: ImpactLevel): string {
  if (level === 'high') return 'Yüksek etki';
  if (level === 'medium') return 'Orta etki';
  return 'Düşük etki';
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '-';
    const diffMin = Math.floor((Date.now() - d.getTime()) / 60000);
    if (diffMin < 1) return 'Az önce';
    if (diffMin < 60) return `${diffMin} dk önce`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH} sa önce`;
    return d.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  } catch {
    return '-';
  }
}

function getDomain(url?: string | null): string {
  if (!url) return '';
  try {
    return new URL(url).hostname.replace(/^www\./, '');
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
  return ['TCMB', 'TUIK', 'TÜİK', 'HMB'].includes(entry.publisher) || cat.includes('macro') || cat.includes('makro') || cat === 'fiscal';
}

function isTurkeySource(entry: FeedEntry): boolean {
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
  return allowedSources.has(entry.publisher) && (!url || allowedDomains.some((domain) => url.includes(domain)));
}

function fromMarketFeedItem(item: MarketFeedItem, index: number): FeedEntry {
  const importance = item.importance_score ?? Math.min(0.9, Math.max(0.25, Math.abs(item.sentiment_score || 0) + 0.35));
  return {
    id: `intel-${item.trigger_id}-${item.timestamp}-${index}`,
    headline: item.headline,
    summary: item.summary ?? item.ai_summary ?? (item.original_headline !== item.headline ? item.original_headline : undefined),
    aiSummary: item.ai_summary ?? item.summary ?? undefined,
    aiAssessment: item.ai_assessment ?? null,
    publisher: item.publisher ?? '',
    symbol: item.symbol,
    category: item.category,
    timestamp: item.timestamp,
    sourceUrl: item.source_url,
    importanceScore: importance,
    type: 'intelligence',
  };
}

function fromKapNotification(item: KapNotification, index: number): FeedEntry {
  return {
    id: `kap-${item.id}-${item.published_at}-${index}`,
    headline: item.title,
    summary: 'KAP bildirimi yayınlandı; şirket etkisi fiyat, hacim ve devam bildirimiyle birlikte izlenmeli.',
    aiSummary: undefined,
    aiAssessment: {
      stance: 'neutral',
      label: 'İzle',
      action: 'KAP devamını kontrol et',
      reasoning: item.symbol ? `${item.symbol} için şirket özelinde resmi bildirim.` : 'Resmi KAP bildirimi.',
      risk: 'Bildirim metni işlem kararından önce detaylı okunmalı.',
      confidence: 0.68,
    },
    publisher: 'KAP',
    symbol: item.symbol,
    timestamp: item.published_at,
    sourceUrl: item.kap_url,
    importanceScore: 0.68,
    type: 'kap',
  };
}

function SkeletonCards() {
  return (
    <div className={styles.feedList}>
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className={styles.skeletonCard}>
          <div className={styles.skeletonMeta} />
          <div className={styles.skeletonTitle} />
          <div className={styles.skeletonBody} />
        </div>
      ))}
    </div>
  );
}

function NewsCard({ entry, expanded, onToggle, isNew }: {
  entry: FeedEntry;
  expanded: boolean;
  onToggle: () => void;
  isNew: boolean;
}) {
  const impact = getImpact(entry.importanceScore);
  const assessment = entry.aiAssessment;

  return (
    <article
      className={`${styles.newsCard} ${expanded ? styles.newsCardExpanded : ''}`}
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') onToggle();
      }}
    >
      <div className={styles.metaRow}>
        <span className={styles.publisher}>{entry.publisher}</span>
        {entry.symbol && <span className={styles.symbol}>{entry.symbol}</span>}
        <span className={styles.time}>{formatTime(entry.timestamp)}</span>
        {isNew && <span className={styles.newBadge}>Yeni</span>}
        <span className={`${styles.impactBadge} ${styles[`impact_${impact}`]}`}>{impactLabel(impact)}</span>
      </div>

      <h2 className={styles.headline}>{entry.headline}</h2>
      {entry.summary && <p className={styles.summary}>{entry.summary}</p>}

      <div className={styles.aiBox}>
        <div>
          <span>AI görüşü</span>
          <strong>{assessment?.label ?? 'İzle'}</strong>
        </div>
        <div>
          <span>Aksiyon</span>
          <strong>{assessment?.action ?? 'Teknik teyit bekle'}</strong>
        </div>
        <div>
          <span>Güven</span>
          <strong>{assessment?.confidence != null ? `${Math.round(assessment.confidence * 100)}%` : '-'}</strong>
        </div>
      </div>

      {expanded && (
        <div className={styles.expanded}>
          {assessment?.reasoning && (
            <p><strong>Gerekçe:</strong> {assessment.reasoning}</p>
          )}
          {assessment?.risk && (
            <p><strong>Risk:</strong> {assessment.risk}</p>
          )}
          {entry.sourceUrl && (
            <a href={entry.sourceUrl} target="_blank" rel="noopener noreferrer" onClick={(event) => event.stopPropagation()}>
              {getDomain(entry.sourceUrl) || 'Kaynağı aç'}
            </a>
          )}
        </div>
      )}
    </article>
  );
}

export default function IntelligencePage() {
  const [entries, setEntries] = useState<FeedEntry[]>([]);
  const [dailySummary, setDailySummary] = useState<string | null>(null);
  const [aiDigest, setAiDigest] = useState<string | null>(null);
  const [sourceSummary, setSourceSummary] = useState<Record<string, number>>({});
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
    if (!options?.silent) setError(null);

    try {
      const [overview, kapFeed] = await Promise.allSettled([
        api.getIntelligenceOverview(60),
        api.getKapFeed(30),
      ]);

      const intelligenceEntries =
        overview.status === 'fulfilled'
          ? overview.value.feed.map(fromMarketFeedItem).filter((entry) => entry.publisher && isTurkeySource(entry))
          : [];
      const kapEntries =
        kapFeed.status === 'fulfilled'
          ? kapFeed.value.map(fromKapNotification).filter((entry) => isTurkeySource(entry))
          : [];

      if (overview.status === 'fulfilled') {
        setAiDigest(overview.value.ai_digest?.summary ?? null);
        setSourceSummary(overview.value.source_summary ?? {});
      }

      const seen = new Set<string>();
      const merged = [...intelligenceEntries, ...kapEntries].filter((entry) => {
        const key = `${entry.sourceUrl ?? ''}|${entry.headline}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      if (merged.length > 0) {
        const previousIds = seenEntryIdsRef.current;
        const nextIds = new Set(merged.map((entry) => entry.id));
        const incomingIds = options?.silent
          ? new Set(merged.filter((entry) => !previousIds.has(entry.id)).map((entry) => entry.id))
          : new Set<string>();

        setEntries(merged);
        setNewEntryIds(incomingIds);
        setLastUpdated(new Date().toISOString());
        seenEntryIdsRef.current = nextIds;
        setError(null);

        if (incomingIds.size > 0) {
          window.setTimeout(() => setNewEntryIds(new Set()), 8000);
        }
      } else if (!options?.silent) {
        setEntries([]);
        setError('Haber akışı şu anda boş. Kaynaklar yeniden denenecek.');
      }

      void api.getDailySummary().then((result) => setDailySummary(result.summary)).catch(() => null);
    } catch (err) {
      if (!options?.silent) {
        setError(err instanceof Error ? err.message : 'Haberler alınamadı');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      loadingRef.current = false;
    }
  }

  const filtered = entries.filter((entry) => {
    if (filter === 'tumu') return true;
    if (filter === 'kap') return isKapItem(entry);
    if (filter === 'resmi') return isOfficialItem(entry);
    if (filter === 'makro') return isMakroItem(entry);
    if (filter === 'piyasa') return !isKapItem(entry) && !isMakroItem(entry);
    return true;
  });

  const topSources = useMemo(() => {
    const fallback = entries.reduce<Record<string, number>>((acc, entry) => {
      acc[entry.publisher] = (acc[entry.publisher] ?? 0) + 1;
      return acc;
    }, {});
    return Object.entries(Object.keys(sourceSummary).length ? sourceSummary : fallback)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [entries, sourceSummary]);

  const sourceCount = new Set(entries.map((entry) => entry.publisher)).size;
  const kapCount = entries.filter(isKapItem).length;
  const highImpactCount = entries.filter((entry) => getImpact(entry.importanceScore) === 'high').length;
  const latestEntry = entries[0];
  const heroSummary = aiDigest || dailySummary || 'Haber akışı hazırlanıyor. Sistem KAP, resmi kurumlar ve Türkiye piyasa kaynaklarını birlikte tarıyor.';

  return (
    <AppShell>
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <span className={styles.eyebrow}>Haber Radarı</span>
            <h1>BIST haber akışı ve AI etkisi</h1>
            <p>{heroSummary}</p>
            <div className={styles.heroFacts}>
              <div>
                <span>Kaynak</span>
                <strong>{sourceCount || '-'}</strong>
              </div>
              <div>
                <span>KAP</span>
                <strong>{kapCount || '-'}</strong>
              </div>
              <div>
                <span>Yüksek etki</span>
                <strong>{highImpactCount || '-'}</strong>
              </div>
            </div>
          </div>

          <aside className={styles.statusCard}>
            <div className={styles.statusTop}>
              <span className={refreshing ? styles.liveRefreshing : styles.liveIdle} />
              <div>
                <strong>{refreshing ? 'Yenileniyor' : 'Canlı akış'}</strong>
                <p>{lastUpdated ? `Son kontrol ${formatTime(lastUpdated)}` : 'İlk veri bekleniyor'}</p>
              </div>
            </div>
            <div className={styles.statusRows}>
              <div>
                <span>Son haber</span>
                <strong>{latestEntry ? formatTime(latestEntry.timestamp) : '-'}</strong>
              </div>
              <div>
                <span>Öncelik</span>
                <strong>KAP + resmi + piyasa</strong>
              </div>
              <div>
                <span>Kapsam</span>
                <strong>Türkiye kaynakları</strong>
              </div>
            </div>
          </aside>
        </section>

        <section className={styles.toolbar}>
          <div className={styles.filterPills}>
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                className={`${styles.pill} ${filter === key ? styles.pillActive : ''}`}
                onClick={() => setFilter(key)}
              >
                {label}
              </button>
            ))}
          </div>
          <button type="button" className={styles.refreshButton} onClick={() => void loadData()}>
            Yenile
          </button>
        </section>

        {error && <div className={styles.errorMsg}>{error}</div>}

        <section className={styles.contentGrid}>
          <div className={styles.feedPanel}>
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.eyebrow}>Akış</span>
                <h2>{filter === 'tumu' ? 'Öne çıkan haberler' : `${FILTERS.find((item) => item.key === filter)?.label} haberleri`}</h2>
              </div>
              <span>{filtered.length} kayıt</span>
            </div>

            {loading ? (
              <SkeletonCards />
            ) : filtered.length === 0 ? (
              <div className={styles.emptyState}>
                <strong>Bu filtrede haber yok</strong>
                <p>Akış geldiğinde burada özet ve AI değerlendirmesiyle gösterilecek.</p>
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

          <aside className={styles.digestPanel}>
            <div className={styles.digestCard}>
              <span className={styles.eyebrow}>Günlük Özet</span>
              <p>{dailySummary || 'Günlük piyasa özeti hazırlanıyor.'}</p>
            </div>

            <div className={styles.digestCard}>
              <span className={styles.eyebrow}>Kaynak Dağılımı</span>
              <div className={styles.sourceList}>
                {topSources.length > 0 ? topSources.map(([source, count]) => (
                  <div key={source}>
                    <span>{source}</span>
                    <strong>{count}</strong>
                  </div>
                )) : (
                  <p className={styles.muted}>Kaynak verisi bekleniyor.</p>
                )}
              </div>
            </div>
          </aside>
        </section>
      </main>
    </AppShell>
  );
}
