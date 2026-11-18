import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppConfig } from '../config';

const mocks = vi.hoisted(() => {
  class InMemoryWebStorage {}
  class WebStorageStateStore {
    store: unknown;
    constructor(options: { store: unknown }) {
      this.store = options.store;
    }
  }
  const instances: Array<{
    settings: Record<string, unknown>;
    signinRedirect: ReturnType<typeof vi.fn>;
    signinCallback: ReturnType<typeof vi.fn>;
    removeUser: ReturnType<typeof vi.fn>;
    clearStaleState: ReturnType<typeof vi.fn>;
  }> = [];
  class UserManager {
    settings: Record<string, unknown>;
    signinRedirect = vi.fn().mockResolvedValue(undefined);
    signinCallback = vi.fn();
    removeUser = vi.fn().mockResolvedValue(undefined);
    clearStaleState = vi.fn().mockResolvedValue(undefined);
    constructor(settings: Record<string, unknown>) {
      this.settings = settings;
      instances.push(this);
    }
  }
  return { InMemoryWebStorage, WebStorageStateStore, UserManager, instances };
});

vi.mock('oidc-client-ts', () => ({
  InMemoryWebStorage: mocks.InMemoryWebStorage,
  WebStorageStateStore: mocks.WebStorageStateStore,
  UserManager: mocks.UserManager,
}));

import { createAuthClient, resetCallbackForTests } from '../auth/authClient';
import { createSessionHolder } from '../auth/sessionHolder';
import { DRAFT_KEY, saveDraft } from '../draft/draftStore';

const CONFIG: AppConfig = {
  apiUrl: 'https://api.example.invalid',
  region: 'us-east-1',
  userPoolId: 'us-east-1_AbCdEf123',
  cognitoDomain: 'agente.auth.us-east-1.amazoncognito.com',
  clientId: 'client123',
  redirectUri: 'http://localhost:3000/',
};

const TOKEN = 'TOKEN-ID-secreto';
const USER = { id_token: TOKEN, profile: { exp: 4_000_000_000 } };

function setup(navigate = vi.fn()) {
  const holder = createSessionHolder(() => 0);
  const client = createAuthClient(CONFIG, holder, { navigate });
  const manager = mocks.instances[mocks.instances.length - 1];
  return { holder, client, manager, navigate };
}

beforeEach(() => {
  mocks.instances.length = 0;
  resetCallbackForTests();
  localStorage.clear();
  sessionStorage.clear();
  window.history.replaceState({}, '', '/');
});

describe('configuración de la biblioteca (NFR4.1, NFR5.1, NFR5.2, NFR5.5)', () => {
  it('usa código con PKCE, alcance openid email, sin renovación ni userinfo y sin secreto', () => {
    const { manager } = setup();

    expect(manager.settings).toMatchObject({
      authority: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_AbCdEf123',
      client_id: 'client123',
      redirect_uri: 'http://localhost:3000/',
      post_logout_redirect_uri: 'http://localhost:3000/',
      response_type: 'code',
      scope: 'openid email',
      loadUserInfo: false,
      automaticSilentRenew: false,
    });
    expect(manager.settings).not.toHaveProperty('client_secret');
  });

  it('declara metadatos explícitos derivados de la configuración pública', () => {
    const { manager } = setup();

    expect(manager.settings.metadata).toMatchObject({
      issuer: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_AbCdEf123',
      authorization_endpoint: 'https://agente.auth.us-east-1.amazoncognito.com/oauth2/authorize',
      token_endpoint: 'https://agente.auth.us-east-1.amazoncognito.com/oauth2/token',
    });
  });

  it('el almacén de usuario es el de memoria y el del estado es sessionStorage', () => {
    const { manager } = setup();
    const userStore = manager.settings.userStore as InstanceType<typeof mocks.WebStorageStateStore>;
    const stateStore = manager.settings.stateStore as InstanceType<
      typeof mocks.WebStorageStateStore
    >;

    expect(userStore).toBeInstanceOf(mocks.WebStorageStateStore);
    expect(userStore.store).toBeInstanceOf(mocks.InMemoryWebStorage);
    expect(stateStore.store).toBe(window.sessionStorage);
  });
});

describe('inicio de sesión (BR5.7, BR5.10)', () => {
  it.each(['Google', 'Microsoft'] as const)(
    'signIn(%s) envía identity_provider exacto',
    async (name) => {
      const { client, manager } = setup();

      await client.signIn(name);

      expect(manager.signinRedirect).toHaveBeenCalledWith({
        extraQueryParams: { identity_provider: name },
      });
    },
  );
});

describe('retorno del acceso (BR5.10, NFR5.2, NFR5.5)', () => {
  it('sin parámetros no hay nada que procesar y la dirección no se toca', async () => {
    const replace = vi.spyOn(window.history, 'replaceState');
    const { client, manager } = setup();

    expect(client.callbackPending()).toBe(false);
    await expect(client.consumeCallback()).resolves.toEqual({ status: 'none' });
    expect(manager.signinCallback).not.toHaveBeenCalled();
    expect(replace).not.toHaveBeenCalled();
    replace.mockRestore();
  });

  it('con code y state válidos guarda el token en memoria y limpia la dirección', async () => {
    window.history.replaceState({}, '', '/?code=abc&state=xyz&otro=1#h');
    const { client, manager, holder } = setup();
    manager.signinCallback.mockResolvedValue(USER);

    const result = await client.consumeCallback();

    expect(result).toEqual({ status: 'signedIn' });
    expect(manager.signinCallback).toHaveBeenCalledWith(
      'http://localhost:3000/?code=abc&state=xyz&otro=1#h',
    );
    expect(window.location.search).toBe('?otro=1');
    expect(window.location.hash).toBe('#h');
    expect(holder.getToken()).toBe(TOKEN);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(TOKEN);
  });

  it('un state distinto (la biblioteca rechaza) es un fallo y la dirección se limpia igual', async () => {
    window.history.replaceState({}, '', '/?code=abc&state=falso');
    const { client, manager, holder } = setup();
    manager.signinCallback.mockRejectedValue(new Error('No matching state found in storage'));

    await expect(client.consumeCallback()).resolves.toEqual({ status: 'error' });

    expect(window.location.search).toBe('');
    expect(holder.getToken()).toBeNull();
  });

  it('un code sin state es un fallo sin intercambiar el código', async () => {
    window.history.replaceState({}, '', '/?code=abc');
    const { client, manager } = setup();

    await expect(client.consumeCallback()).resolves.toEqual({ status: 'error' });

    expect(manager.signinCallback).not.toHaveBeenCalled();
    expect(manager.clearStaleState).toHaveBeenCalled();
    expect(window.location.search).toBe('');
  });

  it.each([
    ['con state', '/?error=access_denied&error_description=cancelado&state=xyz'],
    ['sin state', '/?error=access_denied&error_description=cancelado'],
  ])(
    'un error del proveedor %s es un fallo y se borran error, descripción y state',
    async (_n, url) => {
      window.history.replaceState({}, '', url);
      const { client, manager } = setup();
      manager.signinCallback.mockRejectedValue(new Error('access_denied'));

      await expect(client.consumeCallback()).resolves.toEqual({ status: 'error' });

      expect(window.location.search).toBe('');
    },
  );

  it('un usuario sin token de identidad válido es un fallo', async () => {
    window.history.replaceState({}, '', '/?code=abc&state=xyz');
    const { client, manager, holder } = setup();
    manager.signinCallback.mockResolvedValue({ profile: {} });

    await expect(client.consumeCallback()).resolves.toEqual({ status: 'error' });
    expect(holder.getToken()).toBeNull();
  });

  it('el retorno se procesa exactamente una vez aunque se pida dos veces (StrictMode)', async () => {
    window.history.replaceState({}, '', '/?code=abc&state=xyz');
    const { client, manager } = setup();
    manager.signinCallback.mockResolvedValue(USER);

    const first = client.consumeCallback();
    expect(client.callbackPending()).toBe(true);
    const second = client.consumeCallback();

    expect(second).toBe(first);
    await first;
    expect(manager.signinCallback).toHaveBeenCalledTimes(1);
  });
});

describe('cierre de sesión (BR5.8, NFR5.5)', () => {
  it('sigue el orden DELETE, removeUser, borrado de la copia y navegación exacta', async () => {
    const order: string[] = [];
    const navigate = vi.fn((url: string) => order.push(`navigate:${url}`));
    const { client, manager, holder } = setup(navigate);
    holder.setFromUser(USER);
    saveDraft({ title: 't', context: '', accountId: 'a' });
    manager.removeUser.mockImplementation(async () => {
      order.push('removeUser');
    });

    await client.signOut(async () => {
      order.push('delete');
    });

    expect(order).toEqual([
      'delete',
      'removeUser',
      'navigate:https://agente.auth.us-east-1.amazoncognito.com/logout?client_id=client123&logout_uri=http%3A%2F%2Flocalhost%3A3000%2F',
    ]);
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
    expect(holder.getToken()).toBeNull();
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(TOKEN);
  });

  it('si DELETE falla igual cierra la sesión local y navega', async () => {
    const { client, manager, navigate } = setup();

    await client.signOut(async () => {
      throw new Error('red caída');
    });

    expect(manager.removeUser).toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it('dropSession vacía el usuario en memoria y el token sin navegar', async () => {
    const { client, manager, holder, navigate } = setup();
    holder.setFromUser(USER);

    await client.dropSession();

    expect(manager.removeUser).toHaveBeenCalled();
    expect(holder.getToken()).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });
});
