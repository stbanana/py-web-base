'use client';

import { Theme } from '@carbon/react';
import { createContext, useContext, useEffect, useMemo, useState } from 'react';

type AppTheme = 'white' | 'g90';

type ThemeContextValue = {
  theme: AppTheme;
  setTheme: (theme: AppTheme) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<AppTheme>('white');

  useEffect(() => {
    const savedTheme = window.localStorage.getItem('app-theme');
    if (savedTheme === 'white' || savedTheme === 'g90') {
      setTheme(savedTheme);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem('app-theme', theme);
    document.documentElement.setAttribute('data-app-theme', theme);
  }, [theme]);

  const value = useMemo(() => ({ theme, setTheme }), [theme]);

  return (
    <ThemeContext.Provider value={value}>
      <Theme theme={theme}>{children}</Theme>
    </ThemeContext.Provider>
  );
}

export function useAppTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useAppTheme must be used within AppThemeProvider');
  }
  return context;
}
