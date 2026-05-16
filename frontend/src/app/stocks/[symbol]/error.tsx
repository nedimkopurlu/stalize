'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import AppShell from '@/components/AppShell';
import styles from './page.module.css';

export default function StockDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Stock detail render error', error);
  }, [error]);

  return (
    <AppShell>
      <div className={styles.editorialPage}>
        <section className={styles.errorPanel}>
          <div>
            <div className={styles.sectionEyebrow}>Hisse Detayı</div>
            <h1>Bu hisse ekranı şu an açılamadı</h1>
            <p>
              Veri akışındaki eksik veya bozuk bir alan yakalandı. Sayfa tamamen düşmek yerine burada durdu;
              tekrar deneyebilir ya da tüm hisseler listesine dönebilirsin.
            </p>
          </div>
          <div className={styles.errorActions}>
            <button type="button" className={styles.analyzeBtn} onClick={reset}>
              Yeniden dene
            </button>
            <Link className={styles.secondaryAction} href="/stocks">
              Tüm hisseler
            </Link>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
