import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Root } from './bootstrap';
import AppThemeProvider from './components/AppThemeProvider';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppThemeProvider>
      <Root />
    </AppThemeProvider>
  </StrictMode>,
);
