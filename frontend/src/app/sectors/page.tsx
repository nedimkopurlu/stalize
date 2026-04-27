'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { PriceChange } from '@/components/StockHelpers';
import { TerminalEmpty, TerminalPageHeader, TerminalSection, TerminalShell } from '@/components/TerminalPrimitives';
import api, { SectorSummary } from '@/lib/api';
import styles from './sectors.module.css';

export default function SectorsPage() {
  const [sectors, setSectors] = useState<SectorSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadSectors();
  }, []);

  async function loadSectors() {
    setLoading(true);
    try {
      const res = await api.getSectors();
      setSectors(res.sectors);
    } finally {
      setLoading(false);
    }
  }
  return (
    <AppShell>
        <TerminalShell>
          <TerminalPageHeader
            title="Sektörler"
            description="Sektör dağılımını skor ve günlük yön bilgisiyle izle, ardından aynı filtreyle hisse radarına geç."
            action={(
              <button className="btn btn-primary" onClick={loadSectors} disabled={loading}>
                {loading ? 'Yükleniyor...' : 'Sektörleri Yenile'}
              </button>
            )}
          />
          <TerminalSection
            title="Sektör Kartları"
            description="Kartın içine girildiğinde hisse radarına aynı filtreyle geçilir."
          >
            {loading ? (
              <TerminalEmpty>Sektör verisi hazırlanıyor...</TerminalEmpty>
            ) : (
              <div className={styles.sectorGrid}>
                {sectors.map((sector) => (
                  <Link key={sector.sector} href={`/stocks?sector=${encodeURIComponent(sector.sector)}`} className={`card ${styles.sectorCard}`}>
                    <div className={styles.sectorHeader}>
                      <div className={styles.sectorName}>{sector.sector}</div>
                      <span className="badge badge-blue">{sector.stock_count} hisse</span>
                    </div>
                    <div className={styles.sectorStats}>
                      <div className={styles.sectorStat}>
                        <span className={styles.sectorStatLabel}>Ortalama Skor</span>
                        <strong className={styles.sectorStatValue}>{(sector.avg_score ?? 0).toFixed(1)}</strong>
                      </div>
                      <div className={styles.sectorStat}>
                        <span className={styles.sectorStatLabel}>Ortalama Değişim</span>
                        <div style={{ paddingTop: 6 }}>
                          <PriceChange value={sector.avg_daily_change} />
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </TerminalSection>
        </TerminalShell>
    </AppShell>
  );
}
