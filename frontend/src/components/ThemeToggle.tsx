'use client';

import { useEffect, useSyncExternalStore } from 'react';

type Theme = 'dark' | 'light';

const THEME_KEY = 'stalize-theme';
const THEME_CHANGE_EVENT = 'stalize-theme-change';

function getPreferredTheme(): Theme {
  if (typeof window === 'undefined') return 'dark';
  const stored = window.localStorage.getItem(THEME_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function subscribeTheme(listener: () => void) {
  window.addEventListener('storage', listener);
  window.addEventListener(THEME_CHANGE_EVENT, listener);

  return () => {
    window.removeEventListener('storage', listener);
    window.removeEventListener(THEME_CHANGE_EVENT, listener);
  };
}

export default function ThemeToggle() {
  const theme = useSyncExternalStore(subscribeTheme, getPreferredTheme, () => 'dark');

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    window.localStorage.setItem(THEME_KEY, nextTheme);
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
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
