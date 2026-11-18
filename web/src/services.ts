import { createApiClient, type ApiClient } from './api/client';
import { createAuthClient, type AuthClient } from './auth/authClient';
import { createSessionHolder, type SessionHolder } from './auth/sessionHolder';
import type { AppConfig } from './config';

/** Las piezas con efectos (acceso, servicio y token) que la pantalla recibe ya armadas. */
export interface Services {
  auth: AuthClient;
  api: ApiClient;
  holder: SessionHolder;
}

export function createServices(config: AppConfig): Services {
  const holder = createSessionHolder();
  return {
    holder,
    auth: createAuthClient(config, holder),
    api: createApiClient({ baseUrl: config.apiUrl, getToken: () => holder.getToken() }),
  };
}
