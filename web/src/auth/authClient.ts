/**
 * Envoltura de oidc-client-ts para Cognito (BR5.7, BR5.8, BR5.10; NFR4.1, NFR5.2, NFR5.5).
 * Código con PKCE, token de identidad solo en memoria y retorno procesado una sola vez.
 */
import { InMemoryWebStorage, UserManager, WebStorageStateStore } from 'oidc-client-ts';
import { clearDraft } from '../draft/draftStore';
import type { AppConfig } from '../config';
import type { SessionHolder, UserLike } from './sessionHolder';

/** Nombres exactos de los proveedores del grupo de Cognito (contract-summary, alojamiento). */
export type Provider = 'Google' | 'Microsoft';

export type CallbackResult = { status: 'none' } | { status: 'signedIn' } | { status: 'error' };

export interface AuthClient {
  signIn(provider: Provider): Promise<void>;
  /** Procesa el retorno del acceso exactamente una vez, aunque se pida varias veces. */
  consumeCallback(): Promise<CallbackResult>;
  /** true si la dirección trae un retorno por procesar o ya hay uno en curso. */
  callbackPending(): boolean;
  /** DELETE, removeUser, borrado de la copia y navegación al cierre de Cognito, en ese orden. */
  signOut(deleteSession: () => Promise<unknown>): Promise<void>;
  /** Olvida la sesión en memoria sin navegar (token vencido o rechazado). */
  dropSession(): Promise<void>;
}

export interface AuthClientOptions {
  navigate?: (url: string) => void;
}

const CALLBACK_PARAMS = ['code', 'state', 'error', 'error_description'];

// Variable de módulo (no un efecto de React): el doble efecto de StrictMode reutiliza la promesa.
let callbackPromise: Promise<CallbackResult> | null = null;
let callbackInFlight = false;

export function resetCallbackForTests(): void {
  callbackPromise = null;
  callbackInFlight = false;
}

if (import.meta.hot) {
  import.meta.hot.dispose(resetCallbackForTests);
}

function hasCallbackParams(search: string): boolean {
  const params = new URLSearchParams(search);
  return params.has('code') || params.has('error');
}

/** Borra los parámetros del retorno de la dirección de la página, conservando los demás. */
function cleanAddressBar(): void {
  const url = new URL(window.location.href);
  for (const name of CALLBACK_PARAMS) url.searchParams.delete(name);
  window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
}

export function createAuthClient(
  config: AppConfig,
  holder: SessionHolder,
  options: AuthClientOptions = {},
): AuthClient {
  const navigate = options.navigate ?? ((url: string) => window.location.assign(url));
  const issuer = `https://cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}`;
  const domain = `https://${config.cognitoDomain}`;

  const manager = new UserManager({
    authority: issuer,
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    post_logout_redirect_uri: config.redirectUri,
    response_type: 'code',
    scope: 'openid email',
    loadUserInfo: false,
    automaticSilentRenew: false,
    metadata: {
      issuer,
      authorization_endpoint: `${domain}/oauth2/authorize`,
      token_endpoint: `${domain}/oauth2/token`,
      jwks_uri: `${issuer}/.well-known/jwks.json`,
    },
    // El token vive solo en memoria; el verificador y el estado, solo durante la redirección.
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
  });

  async function runCallback(href: string): Promise<CallbackResult> {
    const params = new URL(href).searchParams;
    try {
      if (params.has('code') && !params.has('state')) {
        await manager.clearStaleState();
        return { status: 'error' };
      }
      const user = (await manager.signinCallback(href)) as UserLike | undefined;
      if (user === undefined || !holder.setFromUser(user)) return { status: 'error' };
      return { status: 'signedIn' };
    } catch {
      // Estado distinto, cancelación o proveedor caído: un solo mensaje propio, sin detalles.
      return { status: 'error' };
    }
  }

  return {
    async signIn(provider) {
      await manager.signinRedirect({ extraQueryParams: { identity_provider: provider } });
    },

    consumeCallback() {
      if (callbackPromise === null) {
        if (!hasCallbackParams(window.location.search)) {
          callbackPromise = Promise.resolve({ status: 'none' });
        } else {
          const captured = window.location.href;
          cleanAddressBar();
          callbackInFlight = true;
          callbackPromise = runCallback(captured).finally(() => {
            callbackInFlight = false;
          });
        }
      }
      return callbackPromise;
    },

    callbackPending() {
      return callbackPromise === null
        ? hasCallbackParams(window.location.search)
        : callbackInFlight;
    },

    async signOut(deleteSession) {
      try {
        await deleteSession();
      } catch {
        // el servicio no guarda estado: el cierre efectivo es el de Cognito
      }
      await manager.removeUser();
      holder.clear();
      clearDraft();
      const query = new URLSearchParams({
        client_id: config.clientId,
        logout_uri: config.redirectUri,
      });
      navigate(`${domain}/logout?${query.toString()}`);
    },

    async dropSession() {
      await manager.removeUser();
      holder.clear();
    },
  };
}
