'use client';

import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window === 'undefined') {
      return 'dark';
    }
    return window.localStorage.getItem('stalize-theme') === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('stalize-theme', theme);
  }, [theme]);

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
