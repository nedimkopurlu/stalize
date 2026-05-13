'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import styles from './Sidebar.module.css';
import ThemeToggle from './ThemeToggle';

// ── SVG Icons ──────────────────────────────────────
function IconGrid() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}

function IconBriefcase() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
    </svg>
  );
}

function IconLayers() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  );
}

function IconSparkles() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
      <path d="M5 18l.75 2.25L8 21l-2.25.75L5 24l-.75-2.25L2 21l2.25-.75L5 18z" />
      <path d="M19 3l.75 2.25L22 6l-2.25.75L19 9l-.75-2.25L16 6l2.25-.75L19 3z" />
    </svg>
  );
}

function IconNewspaper() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
      <path d="M18 14h-8" /><path d="M15 18h-5" /><path d="M10 6h8v4h-8V6Z" />
    </svg>
  );
}

function IconChartBar() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

// ── Nav Items ──────────────────────────────────────
const NAV_ITEMS = [
  { href: '/',                 label: 'Genel Bakış',     Icon: IconGrid       },
  { href: '/portfolio',        label: 'Portföy',         Icon: IconBriefcase  },
  { href: '/stocks',           label: 'Tüm Hisseler',    Icon: IconLayers     },
  { href: '/model-portfolio',  label: 'Model Portföyler',Icon: IconSparkles   },
  { href: '/intelligence',     label: 'Haberler',        Icon: IconNewspaper  },
  { href: '/backtest',         label: 'Backtest',        Icon: IconChartBar   },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className={styles.mobileBar}>
        <button
          type="button"
          className={styles.mobileToggle}
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Menüyü aç"
          aria-expanded={mobileOpen}
        >
          <span />
          <span />
          <span />
        </button>
        <div className={styles.mobileBrand}>
          <div className={styles.logoText}>Stalize</div>
          <div className={styles.logoSub}>BIST Analiz</div>
        </div>
      </div>

      {mobileOpen && (
        <button
          className={styles.overlay}
          aria-label="Menüyü kapat"
          onClick={() => setMobileOpen(false)}
        />
      )}

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
            <div className={styles.logoSub}>BIST Analiz</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className={styles.nav}>
          {NAV_ITEMS.map(({ href, label, Icon }) => {
            const isActive =
              pathname === href ||
              (href !== '/' && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                title={label}
                className={`${styles.navItem} ${isActive ? styles.active : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className={styles.navIcon}>
                  <Icon />
                </span>
                <span className={styles.navLabel}>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className={styles.bottom}>
          <div className={styles.themeRow}>
            <ThemeToggle />
          </div>
        </div>
      </aside>
    </>
  );
}
