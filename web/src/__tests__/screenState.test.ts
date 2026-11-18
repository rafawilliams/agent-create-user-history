import { describe, expect, it } from 'vitest';
import { initialState, reduce, type ScreenState } from '../state/screenState';

const idle = (): ScreenState =>
  reduce(reduce(initialState(), { type: 'signInStarted' }), {
    type: 'sessionConfirmed',
  });

const generating = (): ScreenState => reduce(idle(), { type: 'submitted' });

describe('screenState (ENT-002)', () => {
  it('empieza en signedOut, o en signingIn si hay un retorno de acceso pendiente', () => {
    expect(initialState().kind).toBe('signedOut');
    expect(initialState(true).kind).toBe('signingIn');
  });

  it('signedOut -> signingIn -> idle', () => {
    const signingIn = reduce(initialState(), { type: 'signInStarted' });
    expect(signingIn.kind).toBe('signingIn');
    expect(reduce(signingIn, { type: 'sessionConfirmed' }).kind).toBe('idle');
  });

  it('un fallo de acceso vuelve a S1 con el aviso de acceso', () => {
    const state = reduce(reduce(initialState(), { type: 'signInStarted' }), {
      type: 'signInFailed',
    });
    expect(state).toMatchObject({ kind: 'signedOut', authError: true });
  });

  it('sessionConfirmed pasa a needsContext si había contexto guardado y arrastra el aviso', () => {
    const state = reduce(reduce(initialState(), { type: 'signInStarted' }), {
      type: 'sessionConfirmed',
      needsContext: true,
      notice: 'aviso',
    });
    expect(state).toMatchObject({ kind: 'needsContext', notice: 'aviso' });
  });

  it('submitted pasa a generating y limpia errores, fallo y resultado', () => {
    const failed = reduce(generating(), {
      type: 'failed',
      message: 'm',
      retryable: true,
    });
    const next = reduce(failed, { type: 'submitted' });
    expect(next).toMatchObject({
      kind: 'generating',
      failure: null,
      result: null,
      titleError: null,
      contextError: null,
    });
  });

  it('es imposible enviar dos veces: submitted en generating no cambia nada', () => {
    const state = generating();
    expect(reduce(state, { type: 'submitted' })).toBe(state);
  });

  it.each(['signedOut', 'signingIn', 'sessionExpired', 'accessDenied'] as const)(
    'submitted se ignora en %s',
    (kind) => {
      const state = { ...initialState(), kind };
      expect(reduce(state, { type: 'submitted' })).toBe(state);
    },
  );

  it('generated solo vale en generating y deja el resultado', () => {
    const result = { requestId: 'r', markdown: '# H' };
    expect(reduce(generating(), { type: 'generated', result })).toMatchObject({
      kind: 'result',
      result,
    });
    const state = idle();
    expect(reduce(state, { type: 'generated', result })).toBe(state);
  });

  it('failed deja el mensaje, si se puede reintentar y la hora hasta la que se bloquea', () => {
    const state = reduce(generating(), {
      type: 'failed',
      message: 'msg',
      retryable: true,
      blockedUntil: 123,
    });
    expect(state).toMatchObject({
      kind: 'failed',
      failure: { message: 'msg', retryable: true, retry: 'generate', blockedUntil: 123 },
    });
  });

  it('un fallo al comprobar la sesión ofrece reintentar la comprobación', () => {
    const state = reduce(reduce(initialState(), { type: 'signInStarted' }), {
      type: 'sessionCheckFailed',
      message: 'm',
    });
    expect(state).toMatchObject({
      kind: 'failed',
      failure: { retry: 'session', retryable: true },
    });
  });

  it('needsContext desde generating muestra el mensaje y no deja resultado', () => {
    const state = reduce(generating(), { type: 'needsContext', message: 'pide contexto' });
    expect(state).toMatchObject({
      kind: 'needsContext',
      contextMessage: 'pide contexto',
      result: null,
    });
  });

  it('CONTEXT_TOO_LONG pasa a needsContext con el error del campo de contexto', () => {
    const state = reduce(generating(), { type: 'needsContext', contextError: 'largo' });
    expect(state).toMatchObject({ kind: 'needsContext', contextError: 'largo' });
  });

  it('titleRejected vuelve a idle con el error del título', () => {
    const state = reduce(generating(), { type: 'titleRejected', message: 'vacío' });
    expect(state).toMatchObject({ kind: 'idle', titleError: 'vacío' });
  });

  it('validationFailed deja el estado y marca el campo que corresponde', () => {
    expect(
      reduce(idle(), { type: 'validationFailed', field: 'title', message: 't' }),
    ).toMatchObject({ kind: 'idle', titleError: 't' });
    const needs = reduce(generating(), { type: 'needsContext', message: 'm' });
    expect(
      reduce(needs, { type: 'validationFailed', field: 'context', message: 'c' }),
    ).toMatchObject({ kind: 'needsContext', contextError: 'c' });
  });

  it('edited limpia los errores de campo y libera un fallo no reintentable', () => {
    const withError = reduce(idle(), { type: 'validationFailed', field: 'title', message: 't' });
    expect(reduce(withError, { type: 'edited' }).titleError).toBeNull();

    const final = reduce(generating(), { type: 'failed', message: 'x', retryable: false });
    expect(reduce(final, { type: 'edited' }).kind).toBe('idle');
    const retryable = reduce(generating(), { type: 'failed', message: 'x', retryable: true });
    expect(reduce(retryable, { type: 'edited' }).kind).toBe('failed');
  });

  it('sessionExpired y accessDenied valen desde cualquier estado con sesión y borran el resultado', () => {
    const withResult = reduce(generating(), {
      type: 'generated',
      result: { requestId: 'r', markdown: 'x' },
    });
    expect(reduce(withResult, { type: 'sessionExpired' })).toMatchObject({
      kind: 'sessionExpired',
      result: null,
    });
    expect(reduce(generating(), { type: 'accessDenied' }).kind).toBe('accessDenied');
  });

  it('signedOut vuelve a S1 sin aviso de error', () => {
    const expired = reduce(generating(), { type: 'sessionExpired' });
    expect(reduce(expired, { type: 'signedOut' })).toMatchObject({
      kind: 'signedOut',
      authError: false,
    });
  });
});
