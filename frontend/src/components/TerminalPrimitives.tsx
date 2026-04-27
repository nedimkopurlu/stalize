'use client';

import type { ReactNode } from 'react';
import styles from './terminal.module.css';

export function TerminalShell({ children }: { children: ReactNode }) {
  return <div className={styles.shell}>{children}</div>;
}

export function TerminalPageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <section className={styles.pageHeader}>
      <div className={styles.pageHeaderBody}>
        <h1 className={styles.pageHeaderTitle}>{title}</h1>
        <p className={styles.pageHeaderDescription}>{description}</p>
      </div>
      {action ? <div className={styles.pageHeaderAction}>{action}</div> : null}
    </section>
  );
}

export function TerminalMetric({
  label,
  value,
  note,
}: {
  label: string;
  value: ReactNode;
  note?: string;
}) {
  return (
    <div className={styles.metricCard}>
      <span className={styles.metricCardLabel}>{label}</span>
      <strong className={styles.metricCardValue}>{value}</strong>
      {note ? <span className={styles.metricCardNote}>{note}</span> : null}
    </div>
  );
}

export function TerminalSection({
  title,
  description,
  action,
  children,
  muted = false,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  muted?: boolean;
}) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>{title}</h2>
          {description ? <p className={styles.sectionDescription}>{description}</p> : null}
        </div>
        {action}
      </div>
      <div className={`${styles.panel} ${muted ? styles.panelMuted : ''}`}>{children}</div>
    </section>
  );
}

export function TerminalEmpty({ children }: { children: ReactNode }) {
  return <div className={styles.emptyState}>{children}</div>;
}

export function TerminalError({ children }: { children: ReactNode }) {
  return <div className={styles.errorState}>{children}</div>;
}

export function TerminalKpiList({ children }: { children: ReactNode }) {
  return <div className={styles.kpiList}>{children}</div>;
}

export function TerminalKpiRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className={styles.kpiRow}>
      <span className={styles.kpiLabel}>{label}</span>
      <span className={styles.kpiValue}>{value}</span>
    </div>
  );
}
