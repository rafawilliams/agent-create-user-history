import { Alert, Container } from '@mui/material';
import { useState } from 'react';
import App from './App';
import { ConfigError, loadConfig } from './config';
import { createServices, type Services } from './services';

function ConfigErrorScreen() {
  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Alert severity="error">La pantalla no está configurada. Avisa a quien la administra.</Alert>
    </Container>
  );
}

/**
 * Valida la configuración pública al arrancar (NFR5.1): sin ella la pantalla muestra un error
 * de configuración y no inicia sesión. El mensaje nunca incluye los valores recibidos.
 */
export function Root({ env = import.meta.env }: { env?: Record<string, unknown> }) {
  const [services] = useState<Services | null>(() => {
    try {
      return createServices(loadConfig(env));
    } catch (error) {
      if (error instanceof ConfigError) return null;
      throw error;
    }
  });
  return services === null ? <ConfigErrorScreen /> : <App services={services} />;
}
