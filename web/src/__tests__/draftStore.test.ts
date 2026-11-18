import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DRAFT_KEY, clearDraft, restoreDraft, saveDraft } from '../draft/draftStore';

const DRAFT = { title: 'Recuperar contraseña', context: 'Para usuarios web', accountId: 'acc-1' };

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('draftStore (ENT-003, NFR4.4)', () => {
  it('guarda título, contexto y accountId en sessionStorage bajo una sola clave', () => {
    saveDraft(DRAFT);

    expect(sessionStorage.length).toBe(1);
    expect(JSON.parse(sessionStorage.getItem(DRAFT_KEY) as string)).toEqual(DRAFT);
    expect(localStorage.length).toBe(0);
  });

  it('restaura con la misma cuenta y borra la copia', () => {
    saveDraft(DRAFT);

    expect(restoreDraft('acc-1')).toEqual({ status: 'restored', draft: DRAFT });
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('con otra cuenta descarta la copia y lo informa', () => {
    saveDraft(DRAFT);

    expect(restoreDraft('acc-2')).toEqual({ status: 'discarded' });
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('sin copia devuelve none', () => {
    expect(restoreDraft('acc-1')).toEqual({ status: 'none' });
  });

  it('una copia con forma inválida se descarta como si no hubiera nada', () => {
    sessionStorage.setItem(DRAFT_KEY, '{no es json');
    expect(restoreDraft('acc-1')).toEqual({ status: 'none' });
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();

    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ title: 1 }));
    expect(restoreDraft('acc-1')).toEqual({ status: 'none' });
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('clearDraft borra la copia (salidas de NFR4.4)', () => {
    saveDraft(DRAFT);
    clearDraft();

    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('no lanza si sessionStorage falla al guardar, leer o borrar', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('cuota');
    });
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('bloqueado');
    });
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('bloqueado');
    });

    expect(() => saveDraft(DRAFT)).not.toThrow();
    expect(restoreDraft('acc-1')).toEqual({ status: 'none' });
    expect(() => clearDraft()).not.toThrow();
  });
});
