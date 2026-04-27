'use client';

import type { ReactNode } from 'react';
import Sidebar from './Sidebar';
import styles from './AppShell.module.css';

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <Sidebar />
      <div className={styles.content}>
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
}
