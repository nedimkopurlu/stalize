'use client';

import type { StockFundamentals } from '@/lib/api';

interface Props {
  fundamentals: StockFundamentals | null;
  loading?: boolean;
}

function MetricRow({ label, value, unit = '', decimals = 2 }: {
  label: string;
  value: number | null | undefined;
  unit?: string;
  decimals?: number;
}) {
  const formatted = value != null
    ? `${value.toFixed(decimals)}${unit}`
    : '—';
  const isNull = value == null;
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid rgba(148,163,184,0.06)' }}>
      <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{label}</span>
      <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.9rem', color: isNull ? 'var(--text-muted)' : 'var(--text-primary)' }}>
        {formatted}
      </span>
    </div>
  );
}

export default function FundamentalMetricCard({ fundamentals, loading }: Props) {
  const title = (
    <div style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 12 }}>
      Temel Metrikler
      {fundamentals?.period && (
        <span style={{ marginLeft: 8, fontWeight: 400, fontSize: '0.7rem', opacity: 0.7 }}>({fundamentals.period})</span>
      )}
    </div>
  );

  if (loading) {
    return (
      <div>
        {title}
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Yükleniyor...</p>
      </div>
    );
  }

  if (!fundamentals) {
    return (
      <div>
        {title}
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Temel veri bulunamadı</p>
      </div>
    );
  }

  return (
    <div>
      {title}
      <MetricRow label="F/K (P/E)" value={fundamentals.pe_ratio} />
      <MetricRow label="PD/DD (P/B)" value={fundamentals.pb_ratio} />
      <MetricRow
        label="ROE"
        value={fundamentals.roe != null ? fundamentals.roe * 100 : null}
        unit="%"
        decimals={1}
      />
      <MetricRow
        label="Net Marj"
        value={fundamentals.net_margin != null ? fundamentals.net_margin * 100 : null}
        unit="%"
        decimals={1}
      />
      <MetricRow label="Borç/Özsermaye" value={fundamentals.debt_to_equity} />
    </div>
  );
}
