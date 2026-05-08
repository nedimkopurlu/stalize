'use client';

import { useEffect, useState } from 'react';

function getPreferredTheme(): 'dark' | 'light' {
  const stored = window.localStorage.getItem('stalize-theme');
  if (stored === 'light' || stored === 'dark') return stored;
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    setTheme(getPreferredTheme());
    setHasHydrated(true);
  }, []);

  useEffect(() => {
    if (!hasHydrated) return;
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('stalize-theme', theme);
  }, [hasHydrated, theme]);

  function toggleTheme() {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  }

  return (
    <button type="button" className="theme-toggle" onClick={toggleTheme} aria-label="Temayı değiştir">
      <span className="theme-toggle__track">
        <span className={`theme-toggle__thumb ${theme === 'light' ? 'theme-toggle__thumb_light' : ''}`} />
      </span>
      <span className="theme-toggle__label">{theme === 'dark' ? 'Koyu' : 'Açık'}</span>
    </button>
  );
}
