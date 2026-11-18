import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createSessionHolder } from '../auth/sessionHolder';

const TOKEN = 'TOKEN-DE-PRUEBA-abc.def.ghi';

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe('sessionHolder (BR5.6, NFR4.1, NFR4.2)', () => {
  it('guarda el token de identidad y expone su exp', () => {
    const holder = createSessionHolder(() => 1_000_000);

    expect(holder.setFromUser({ id_token: TOKEN, profile: { exp: 2_000 } })).toBe(true);

    expect(holder.getToken()).toBe(TOKEN);
    expect(holder.getExpiresAt()).toBe(2_000);
  });

  it('no entrega nada si el token venció (comparado con el reloj)', () => {
    let nowMs = 1_000_000;
    const holder = createSessionHolder(() => nowMs);
    holder.setFromUser({ id_token: TOKEN, profile: { exp: 1_100 } });

    expect(holder.getToken()).toBe(TOKEN);
    nowMs = 1_100_000;
    expect(holder.getToken()).toBeNull();
  });

  it('no escribe el token en localStorage ni en sessionStorage', () => {
    const holder = createSessionHolder(() => 0);
    holder.setFromUser({ id_token: TOKEN, profile: { exp: 9_999_999_999 } });

    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(TOKEN);
  });

  it('rechaza un usuario sin token de identidad o sin exp', () => {
    const holder = createSessionHolder(() => 0);

    expect(holder.setFromUser({ profile: { exp: 100 } })).toBe(false);
    expect(holder.setFromUser({ id_token: TOKEN, profile: {} })).toBe(false);
    expect(holder.getToken()).toBeNull();
    expect(holder.getExpiresAt()).toBeNull();
  });

  it('clear olvida el token y su exp', () => {
    const holder = createSessionHolder(() => 0);
    holder.setFromUser({ id_token: TOKEN, profile: { exp: 100 } });

    holder.clear();

    expect(holder.getToken()).toBeNull();
    expect(holder.getExpiresAt()).toBeNull();
  });

  it('no escribe el token en la consola', () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((method) =>
      vi.spyOn(console, method).mockImplementation(() => undefined),
    );
    const holder = createSessionHolder(() => 0);

    holder.setFromUser({ id_token: TOKEN, profile: { exp: 100 } });
    holder.getToken();
    holder.clear();

    for (const spy of spies) expect(spy).not.toHaveBeenCalled();
    vi.restoreAllMocks();
  });
});
