import { vi } from 'vitest';
import type { ApiClient } from '../api/client';
import type { AuthClient } from '../auth/authClient';
import { createSessionHolder } from '../auth/sessionHolder';
import type { Services } from '../services';

export const TOKEN = 'TOKEN-ID-secreto-123';
export const TOKEN_EXP_SECONDS = 2_000;

export interface FakeOptions {
  /** Resultado del retorno del acceso al arrancar. */
  callback?: 'none' | 'signedIn' | 'error';
  /** Retraso del retorno: una promesa que el test resuelve a mano. */
  callbackGate?: Promise<void>;
}

export interface Fakes {
  services: Services;
  clock: { now: number };
  auth: { [K in keyof AuthClient]: ReturnType<typeof vi.fn> };
  api: { [K in keyof ApiClient]: ReturnType<typeof vi.fn> };
}

export function makeFakes({ callback = 'signedIn', callbackGate }: FakeOptions = {}): Fakes {
  const clock = { now: 1_000_000 };
  const holder = createSessionHolder(() => clock.now);

  const auth = {
    signIn: vi.fn().mockResolvedValue(undefined),
    consumeCallback: vi.fn(async () => {
      if (callbackGate) await callbackGate;
      if (callback === 'signedIn') {
        holder.setFromUser({ id_token: TOKEN, profile: { exp: TOKEN_EXP_SECONDS } });
      }
      return { status: callback } as const;
    }),
    callbackPending: vi.fn(() => callback !== 'none'),
    signOut: vi.fn(async (deleteSession: () => Promise<unknown>) => {
      try {
        await deleteSession();
      } catch {
        // igual que la implementación real: un fallo del DELETE no detiene el cierre
      }
      holder.clear();
    }),
    dropSession: vi.fn(async () => holder.clear()),
  };

  const api = {
    generateStory: vi.fn(),
    getSession: vi.fn().mockResolvedValue({ accountId: 'acc-1' }),
    deleteSession: vi.fn().mockResolvedValue(undefined),
  };

  return {
    services: { auth: auth as unknown as AuthClient, api: api as unknown as ApiClient, holder },
    clock,
    auth,
    api,
  };
}
