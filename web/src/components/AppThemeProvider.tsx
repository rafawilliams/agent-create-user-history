import { CssBaseline, ThemeProvider, useMediaQuery } from '@mui/material';
import { useEffect, useMemo, type ReactNode } from 'react';
import { createAppTheme } from '../theme';

/** Elige el tema claro u oscuro según la preferencia del sistema (BR5.9). */
export default function AppThemeProvider({ children }: { children: ReactNode }) {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)', { noSsr: true });
  const mode = prefersDark ? 'dark' : 'light';
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  useEffect(() => {
    document.documentElement.dataset.themeMode = mode;
  }, [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline enableColorScheme />
      {children}
    </ThemeProvider>
  );
}
