'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import styles from './Sidebar.module.css';
import ThemeToggle from './ThemeToggle';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', short: '01', note: 'Genel görünüm' },
  { href: '/stocks', label: 'Hisse Radarı', short: '02', note: 'Seçim ve filtreleme' },
  { href: '/screener', label: 'Tarama', short: '03', note: 'Filtrele ve keşfet' },
  { href: '/intelligence', label: 'Piyasa Akışı', short: '04', note: 'KAP ve etkili haberler' },
  { href: '/sectors', label: 'Sektörler', short: '05', note: 'Sektör dağılımı' },
  { href: '/rankings', label: 'Sıralama', short: '06', note: 'Liderlik tablosu' },
  { href: '/model-portfolio', label: 'Model Portföy', short: '07', note: 'Sistemin haftalık seçimi' },
  { href: '/watchlist', label: 'İzleme Listesi', short: '08', note: 'Takip ettiğin hisseler' },
  { href: '/portfolio', label: 'Portföyüm', short: '09', note: 'Kişisel portföy yönetimi' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <div className={styles.mobileBar}>
        <button
          type="button"
          className={styles.mobileToggle}
          onClick={() => setMobileOpen((value) => !value)}
          aria-label="Menüyü aç"
          aria-expanded={mobileOpen}
        >
          <span />
          <span />
          <span />
        </button>
        <div className={styles.mobileBrand}>
          <div className={styles.logoText}>Stalize</div>
          <div className={styles.logoSub}>BIST100 Çalışma Alanı</div>
        </div>
      </div>

      {mobileOpen ? <button className={styles.overlay} aria-label="Menüyü kapat" onClick={() => setMobileOpen(false)} /> : null}

      <aside className={`${styles.sidebar} ${mobileOpen ? styles.open : ''}`}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <defs>
                <linearGradient id="logoGrad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#f59e0b" />
                  <stop offset="0.55" stopColor="#ea580c" />
                  <stop offset="1" stopColor="#f59e0b" />
                </linearGradient>
              </defs>
              <rect width="28" height="28" rx="7" fill="url(#logoGrad)" opacity="0.15" />
              <path d="M7 20L11 12L15 16L21 8" stroke="url(#logoGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="21" cy="8" r="2" fill="#f59e0b" />
            </svg>
          </div>
          <div>
            <div className={styles.logoText}>Stalize</div>
            <div className={styles.logoSub}>BIST Analiz Terminali</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className={styles.nav}>
            <div className={styles.navLabel}>Yatırım Terminali</div>
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${isActive ? styles.active : ''}`}
              onClick={() => setMobileOpen(false)}
            >
                <span className={styles.navIcon}>{item.short}</span>
                <span className={styles.navTextWrap}>
                  <span className={styles.navText}>{item.label}</span>
                  <span className={styles.navNote}>{item.note}</span>
                </span>
                {isActive && <span className={styles.activeIndicator} />}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className={styles.bottom}>
          <div className={styles.statusCard}>
            <div className={styles.statusDot} />
            <div>
              <div className={styles.statusTitle}>Odak</div>
              <div className={styles.statusSub}>Hisse seçimi, tarama, model portföy ve kişisel takip</div>
            </div>
          </div>
          <div className={styles.themeCard}>
            <div>
              <div className={styles.statusTitle}>Tema</div>
              <div className={styles.statusSub}>Görünümü buradan değiştir</div>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </aside>
    </>
  );
}
