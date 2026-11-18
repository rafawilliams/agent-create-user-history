import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { API_TIMEOUT_MS, ApiFailure, createApiClient, type FailureKind } from '../api/client';

const fetchMock = vi.fn();
const BASE = 'https://api.example.invalid';
const TOKEN = 'TOKEN-ID';

function makeClient(getToken: () => string | null = () => TOKEN) {
  return createApiClient({ baseUrl: BASE, getToken });
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

async function failureOf(promise: Promise<unknown>): Promise<ApiFailure> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(ApiFailure);
    return error as ApiFailure;
  }
  throw new Error('se esperaba un fallo');
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('generateStory (C1; BR5.2, NFR1.1)', () => {
  it('envía POST /v1/stories con Authorization Bearer, título y contexto', async () => {
    fetchMock.mockResolvedValue(json(200, { requestId: 'r-1', markdown: '# Historia' }));

    const result = await makeClient().generateStory({ title: 'Login', context: 'Para admins' });

    expect(result).toEqual({ requestId: 'r-1', markdown: '# Historia' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE}/v1/stories`);
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual({ title: 'Login', context: 'Para admins' });
  });

  it('omite el contexto cuando no hay o está vacío', async () => {
    fetchMock.mockResolvedValue(json(200, { requestId: 'r', markdown: 'x' }));

    await makeClient().generateStory({ title: 'Recuperar contraseña', context: '' });

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ title: 'Recuperar contraseña' });
  });

  it('sin token vigente falla como sesión vencida sin llamar al servicio', async () => {
    const failure = await failureOf(makeClient(() => null).generateStory({ title: 'x' }));

    expect(failure.kind).toBe('sessionInvalid');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  const rows: Array<[string, number, Record<string, unknown>, FailureKind, boolean]> = [
    ['NEEDS_CONTEXT', 422, { code: 'NEEDS_CONTEXT', retryable: false }, 'needsContext', false],
    [
      'CONTEXT_TOO_LONG',
      400,
      { code: 'CONTEXT_TOO_LONG', retryable: false },
      'contextTooLong',
      false,
    ],
    ['TITLE_EMPTY', 400, { code: 'TITLE_EMPTY', retryable: false }, 'titleEmpty', false],
    ['TITLE_TOO_LONG', 400, { code: 'TITLE_TOO_LONG', retryable: false }, 'titleTooLong', false],
    ['RATE_LIMITED', 429, { code: 'RATE_LIMITED', retryable: true }, 'rateLimited', true],
    [
      'SESSION_INVALID',
      401,
      { code: 'SESSION_INVALID', retryable: false },
      'sessionInvalid',
      false,
    ],
    [
      'ACCOUNT_NOT_ALLOWED',
      403,
      { code: 'ACCOUNT_NOT_ALLOWED', retryable: false },
      'accessDenied',
      false,
    ],
    ['GENERATION_TIMEOUT', 504, { code: 'GENERATION_TIMEOUT', retryable: true }, 'failed', true],
    ['MODEL_FAILURE', 502, { code: 'MODEL_FAILURE', retryable: true }, 'failed', true],
    [
      'INVALID_MODEL_RESPONSE',
      502,
      { code: 'INVALID_MODEL_RESPONSE', retryable: true },
      'failed',
      true,
    ],
    ['código desconocido', 500, { code: 'ALGO_NUEVO', retryable: true }, 'failed', true],
    ['no reintentable', 502, { code: 'MODEL_FAILURE', retryable: false }, 'failed', false],
  ];

  it.each(rows)('traduce %s a su fila de BR5.4', async (_name, status, body, kind, retryable) => {
    fetchMock.mockResolvedValue(json(status, { ...body, message: 'texto del servicio' }));

    const failure = await failureOf(makeClient().generateStory({ title: 'x' }));

    expect(failure.kind).toBe(kind);
    expect(failure.retryable).toBe(retryable);
  });

  it('nunca muestra el texto del servicio ni nada del cuerpo', async () => {
    fetchMock.mockResolvedValue(
      json(502, { code: 'MODEL_FAILURE', message: 'DETALLE <b>INTERNO</b>', retryable: true }),
    );

    const failure = await failureOf(makeClient().generateStory({ title: 'x' }));

    expect(failure.message).toBe('No se pudo generar la historia. Inténtalo de nuevo.');
    expect(failure.message).not.toContain('INTERNO');
  });

  it('los mensajes de cada tipo son los literales de BR5.4', async () => {
    const messages: Record<string, string> = {
      RATE_LIMITED: 'Hay demasiadas solicitudes. Espera 30 segundos e inténtalo de nuevo.',
      SESSION_INVALID: 'Tu sesión terminó. Inicia sesión de nuevo para continuar.',
      ACCOUNT_NOT_ALLOWED: 'Tu cuenta no tiene acceso a este agente.',
      CONTEXT_TOO_LONG: 'El contexto no puede superar 500 caracteres.',
      TITLE_EMPTY: 'Escribe un titulo para generar la historia.',
      TITLE_TOO_LONG: 'El titulo no puede superar 200 caracteres.',
    };
    for (const [code, message] of Object.entries(messages)) {
      fetchMock.mockResolvedValueOnce(json(400, { code, message: 'x', retryable: false }));
      const failure = await failureOf(makeClient().generateStory({ title: 'x' }));
      expect(failure.message).toBe(message);
    }
  });

  it.each([
    [
      'cuerpo que no es JSON (502 de la pasarela)',
      () => new Response('<html>502</html>', { status: 502 }),
    ],
    ['429 de la pasarela sin code', () => json(429, { message: 'Too Many Requests' })],
    ['504 de la pasarela sin cuerpo', () => new Response('', { status: 504 })],
    ['200 sin markdown', () => json(200, { requestId: 'r' })],
    ['200 con markdown que no es texto', () => json(200, { requestId: 'r', markdown: 42 })],
    ['200 con markdown vacío', () => json(200, { requestId: 'r', markdown: '' })],
    ['200 que no es JSON', () => new Response('no json', { status: 200 })],
  ])('%s es un fallo genérico reintentable', async (_name, makeResponse) => {
    fetchMock.mockResolvedValue(makeResponse());

    const failure = await failureOf(makeClient().generateStory({ title: 'x' }));

    expect(failure.kind).toBe('failed');
    expect(failure.retryable).toBe(true);
    expect(failure.message).toBe('No se pudo generar la historia. Inténtalo de nuevo.');
  });

  it('una red caída es un fallo genérico reintentable', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    const failure = await failureOf(makeClient().generateStory({ title: 'x' }));

    expect(failure).toMatchObject({ kind: 'failed', retryable: true });
  });

  it('no reintenta por su cuenta: un fallo es una sola solicitud', async () => {
    fetchMock.mockResolvedValue(json(502, { code: 'MODEL_FAILURE', retryable: true }));

    await failureOf(makeClient().generateStory({ title: 'x' }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('corta a los 60 s con el mensaje propio y aborta la solicitud', async () => {
    vi.useFakeTimers();
    let signal!: AbortSignal;
    fetchMock.mockImplementation((_url: string, init: RequestInit) => {
      signal = init.signal as AbortSignal;
      return new Promise(() => undefined);
    });

    const pending = failureOf(makeClient().generateStory({ title: 'x' }));
    await vi.advanceTimersByTimeAsync(API_TIMEOUT_MS);
    const failure = await pending;

    expect(API_TIMEOUT_MS).toBe(60_000);
    expect(failure).toMatchObject({ kind: 'timeout', retryable: true });
    expect(failure.message).toBe('La generación superó los 60 segundos. Inténtalo de nuevo.');
    expect(signal.aborted).toBe(true);
  });

  it('una respuesta que llega después del corte se descarta', async () => {
    vi.useFakeTimers();
    let resolveFetch!: (response: Response) => void;
    fetchMock.mockReturnValue(new Promise<Response>((resolve) => (resolveFetch = resolve)));

    const pending = failureOf(makeClient().generateStory({ title: 'x' }));
    await vi.advanceTimersByTimeAsync(API_TIMEOUT_MS);
    resolveFetch(json(200, { requestId: 'tarde', markdown: 'tarde' }));

    expect((await pending).kind).toBe('timeout');
  });

  it('una respuesta justo antes de los 60 s sí se acepta', async () => {
    vi.useFakeTimers();
    let resolveFetch!: (response: Response) => void;
    fetchMock.mockReturnValue(new Promise<Response>((resolve) => (resolveFetch = resolve)));

    const pending = makeClient().generateStory({ title: 'x' });
    await vi.advanceTimersByTimeAsync(API_TIMEOUT_MS - 1);
    resolveFetch(json(200, { requestId: 'r', markdown: 'ok' }));

    await expect(pending).resolves.toEqual({ requestId: 'r', markdown: 'ok' });
  });

  it('no hace ninguna solicitud por sí solo al crearse', () => {
    makeClient();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('getSession y deleteSession (C2)', () => {
  it('GET /v1/session con Bearer devuelve el accountId', async () => {
    fetchMock.mockResolvedValue(
      json(200, {
        sessionId: 's',
        accountId: 'acc-1',
        provider: 'google',
        expiresAt: '2030-01-01T00:00:00Z',
      }),
    );

    await expect(makeClient().getSession()).resolves.toEqual({ accountId: 'acc-1' });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${BASE}/v1/session`);
    expect(init.method).toBe('GET');
    expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
  });

  it.each([
    [401, 'SESSION_INVALID', 'sessionInvalid'],
    [403, 'ACCOUNT_NOT_ALLOWED', 'accessDenied'],
    [500, 'MODEL_FAILURE', 'failed'],
  ])('GET con %i/%s se traduce a %s', async (status, code, kind) => {
    fetchMock.mockResolvedValue(json(status, { code, message: 'x', retryable: false }));

    expect((await failureOf(makeClient().getSession())).kind).toBe(kind);
  });

  it('GET con 200 sin accountId o con red caída es un fallo genérico', async () => {
    fetchMock.mockResolvedValueOnce(json(200, { sessionId: 's' }));
    expect((await failureOf(makeClient().getSession())).kind).toBe('failed');

    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    expect((await failureOf(makeClient().getSession())).kind).toBe('failed');
  });

  it('DELETE /v1/session con 204 termina bien y con error lanza el fallo', async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    await expect(makeClient().deleteSession()).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE');

    fetchMock.mockResolvedValueOnce(json(500, { code: 'X', message: 'x', retryable: true }));
    expect((await failureOf(makeClient().deleteSession())).kind).toBe('failed');
  });

  it('DELETE sin token no llama al servicio', async () => {
    const failure = await failureOf(makeClient(() => null).deleteSession());

    expect(failure.kind).toBe('sessionInvalid');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
