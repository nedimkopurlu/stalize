'use client';

import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import {
  TerminalShell,
  TerminalPageHeader,
  TerminalEmpty,
  TerminalError,
} from '@/components/TerminalPrimitives';
import {
  PriceChange,
  formatPrice,
  formatVolume,
} from '@/components/StockHelpers';
import {
  api,
  MarketBist100Response,
  MarketForexResponse,
  MarketGoldResponse,
  ForexPair,
} from '@/lib/api';
import styles from './page.module.css';

const REFRESH_SECONDS = 30;

const FOREX_TR_LABELS: Record<string, string> = {
  'USDTRY=X': 'Dolar',
  'EURTRY=X': 'Avro',
  'GBPTRY=X': 'Sterlin',
  'CNYTRY=X': 'Çin Yuanı',
  'JPYTRY=X': 'Japon Yeni',
  'CHFTRY=X': 'İsviçre Frangı',
};

const GOLD_TR_LABELS: Record<string, string> = {
  gram: 'Gram Altın',
  ons: 'Ons Altın',
  ceyrek: 'Çeyrek Altın',
  yarim: 'Yarım Altın',
  tam: 'Tam Altın',
};
const GOLD_FORM_ORDER = ['gram', 'ons', 'ceyrek', 'yarim', 'tam'] as const;
type GoldKey = typeof GOLD_FORM_ORDER[number];

export default function DashboardPage() {
  const [bist100, setBist100] = useState<MarketBist100Response | null>(null);
  const [bist100Loading, setBist100Loading] = useState(true);
  const [bist100Error, setBist100Error] = useState<string | null>(null);

  const [forex, setForex] = useState<MarketForexResponse | null>(null);
  const [forexLoading, setForexLoading] = useState(true);
  const [forexError, setForexError] = useState<string | null>(null);

  const [gold, setGold] = useState<MarketGoldResponse | null>(null);
  const [goldLoading, setGoldLoading] = useState(true);
  const [goldError, setGoldError] = useState<string | null>(null);

  const [countdown, setCountdown] = useState(REFRESH_SECONDS);

  useEffect(() => {
    const fetchAll = () => {
      api.getMarketBist100()
        .then((data) => { setBist100(data); setBist100Error(null); })
        .catch(() => setBist100Error('BIST100 verisi alınamadı. Sayfa yenilendiğinde tekrar denenecek.'))
        .finally(() => setBist100Loading(false));

      api.getMarketForex()
        .then((data) => { setForex(data); setForexError(null); })
        .catch(() => setForexError('Döviz verisi alınamadı. Sayfa yenilendiğinde tekrar denenecek.'))
        .finally(() => setForexLoading(false));

      api.getMarketGold()
        .then((data) => { setGold(data); setGoldError(null); })
        .catch(() => setGoldError('Altın verisi alınamadı. Sayfa yenilendiğinde tekrar denenecek.'))
        .finally(() => setGoldLoading(false));
    };

    fetchAll();
    let secs = REFRESH_SECONDS;
    const tick = setInterval(() => {
      secs -= 1;
      if (secs <= 0) {
        secs = REFRESH_SECONDS;
        fetchAll();
      }
      setCountdown(secs);
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  return (
    <AppShell>
      <TerminalShell>
        <TerminalPageHeader
          title="Piyasa Özeti"
          description="BIST100, döviz ve altın — canlı piyasa nabzı"
        />

        <div className={styles.page}>
          {/* ─── BIST100 Banner ─── */}
          <section className={`card ${styles.bist100Banner}`} aria-label="BIST100 Endeksi">
            {bist100Error ? (
              <TerminalError>{bist100Error}</TerminalError>
            ) : !bist100 && bist100Loading ? (
              <div className={`skeleton ${styles.bannerSkeleton}`} style={{ width: '100%' }} />
            ) : (
              <>
                <div>
                  <div className={styles.bist100Eyebrow}>BIST100 ENDEKSİ</div>
                  <div className={styles.bist100Value}>{formatPrice(bist100?.value ?? null)}</div>
                </div>
                <div>
                  <div className={styles.bist100MetaLabel}>Günlük Değişim</div>
                  <div className={styles.bist100Change}>
                    <PriceChange value={bist100?.daily_change_pct ?? null} />
                  </div>
                </div>
                <div className={styles.bist100Meta}>
                  <div className={styles.bist100MetaLabel}>İşlem Hacmi</div>
                  <div className={styles.bist100MetaValue}>{formatVolume(bist100?.volume ?? null)}</div>
                </div>
              </>
            )}
          </section>

          {/* ─── Döviz + Altın Grid ─── */}
          <div className={styles.marketGrid}>
            {/* Döviz */}
            <section className="card" aria-label="Döviz">
              <header className={styles.widgetHeader}>
                <h2 className={styles.widgetTitle}>Döviz</h2>
                <span className={styles.widgetRefreshHint}>Otomatik yenileme: {countdown}s</span>
              </header>
              {forexError ? (
                <TerminalError>{forexError}</TerminalError>
              ) : !forex && forexLoading ? (
                <ForexSkeleton />
              ) : (
                <ForexList pairs={forex?.pairs ?? []} />
              )}
            </section>

            {/* Altın */}
            <section className="card" aria-label="Altın">
              <header className={styles.widgetHeader}>
                <h2 className={styles.widgetTitle}>Altın</h2>
                <span className={styles.widgetRefreshHint}>Otomatik yenileme: {countdown}s</span>
              </header>
              {goldError ? (
                <TerminalError>{goldError}</TerminalError>
              ) : !gold && goldLoading ? (
                <GoldSkeleton />
              ) : (
                <GoldList forms={gold?.forms ?? null} />
              )}
            </section>
          </div>

          {/* ─── Portföy Özet (Plan 02 ekleyecek) ─── */}
          <section className={styles.portfolioPlaceholder} aria-label="Portföyüm">
            <h2 className={styles.widgetTitle} style={{ marginBottom: 16 }}>Portföyüm</h2>
            <TerminalEmpty>
              Henüz portföy eklenmedi. Alım-satım işlemlerinizi girdikten sonra toplam değer ve günlük değişiminiz burada görünür. (Portföy yönetimi yakında)
            </TerminalEmpty>
          </section>
        </div>
      </TerminalShell>
    </AppShell>
  );
}

/* ─── Sub Components ─── */

function ForexList({ pairs }: { pairs: ForexPair[] }) {
  if (pairs.length === 0) {
    return <TerminalEmpty>Döviz verisi henüz hazır değil.</TerminalEmpty>;
  }
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
      {pairs.map((p) => (
        <li key={p.symbol} className={styles.pairRow}>
          <span className={styles.pairLabel}>{FOREX_TR_LABELS[p.symbol] ?? p.name}</span>
          <span className={styles.pairRight}>
            <span className={styles.pairPrice}>₺{formatPrice(p.rate)}</span>
            <PriceChange value={p.daily_change_pct} />
          </span>
        </li>
      ))}
    </ul>
  );
}

function GoldList({ forms }: { forms: MarketGoldResponse['forms'] | null }) {
  if (!forms) {
    return <TerminalEmpty>Altın verisi henüz hazır değil.</TerminalEmpty>;
  }
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
      {GOLD_FORM_ORDER.map((key: GoldKey) => (
        <li key={key} className={styles.pairRow}>
          <span className={styles.pairLabel}>{GOLD_TR_LABELS[key]}</span>
          <span className={styles.pairRight}>
            <span className={styles.pairPrice}>₺{formatPrice(forms[key])}</span>
            {/* Gold change_pct unavailable from backend (Phase 28 limitation) — render "—" */}
            <PriceChange value={null} />
          </span>
        </li>
      ))}
    </ul>
  );
}

function ForexSkeleton() {
  return (
    <div className={styles.listSkeleton}>
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className={`skeleton ${styles.listSkeletonRow}`} />
      ))}
    </div>
  );
}

function GoldSkeleton() {
  return (
    <div className={styles.listSkeleton}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className={`skeleton ${styles.listSkeletonRow}`} />
      ))}
    </div>
  );
}
