'use client';

import type { KapNewsItem } from '@/lib/api';

interface Props {
  news: KapNewsItem[];
  loading?: boolean;
}

function categoryLabel(cat: string | null): string {
  const map: Record<string, string> = {
    geopolitics: 'Jeopolitik',
    macro: 'Makro',
    sector: 'Sektör',
    company: 'Şirket',
  };
  return cat ? (map[cat] ?? cat) : 'Genel';
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return iso;
  }
}

export default function KAPNewsCard({ news, loading }: Props) {
  const header = (
    <div style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12 }}>
      Son KAP Bildirimleri
    </div>
  );

  if (loading) {
    return <div>{header}<p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Yükleniyor...</p></div>;
  }

  if (news.length === 0) {
    return <div>{header}<p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Henüz bildirim yok</p></div>;
  }

  return (
    <div>
      {header}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {news.map((item) => (
          <div key={item.id} style={{ padding: '10px 0', borderBottom: '1px solid rgba(148,163,184,0.06)' }}>
            {/* Başlık — tıklanabilir dış link */}
            {item.url ? (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                  fontWeight: 500,
                  lineHeight: 1.4,
                  textDecoration: 'none',
                  display: 'block',
                  marginBottom: 4,
                  transition: 'color 150ms ease',
                }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--accent-cyan)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-primary)')}
              >
                {item.title}
              </a>
            ) : (
              <span style={{ color: 'var(--text-primary)', fontSize: '0.85rem', fontWeight: 500, lineHeight: 1.4, display: 'block', marginBottom: 4 }}>
                {item.title}
              </span>
            )}
            {/* Meta: tarih + kategori + kaynak */}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{formatDate(item.published_at)}</span>
              {item.category && (
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  padding: '1px 6px',
                  borderRadius: 4,
                  background: 'rgba(148,163,184,0.08)',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  {categoryLabel(item.category)}
                </span>
              )}
              {item.source && (
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', opacity: 0.7 }}>{item.source}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
