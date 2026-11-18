/**
 * Cliente de C1 (POST /v1/stories) y C2 (GET y DELETE /v1/session) con el token de identidad.
 * Un temporizador de 60 s por solicitud, sin reintentos automáticos, y una tabla fija de errores
 * (BR5.4): nunca se muestra texto del servicio ni nada del cuerpo de la respuesta.
 */
import {
  CONTEXT_TOO_LONG_MESSAGE,
  TITLE_EMPTY_MESSAGE,
  TITLE_TOO_LONG_MESSAGE,
} from '../validation';
import type { StoryResult } from '../state/screenState';

export const API_TIMEOUT_MS = 60_000;

export type FailureKind =
  | 'needsContext'
  | 'contextTooLong'
  | 'titleEmpty'
  | 'titleTooLong'
  | 'rateLimited'
  | 'sessionInvalid'
  | 'accessDenied'
  | 'timeout'
  | 'failed';

export const GENERIC_FAILURE_MESSAGE = 'No se pudo generar la historia. Inténtalo de nuevo.';
export const SESSION_EXPIRED_MESSAGE = 'Tu sesión terminó. Inicia sesión de nuevo para continuar.';

export const ACCESS_DENIED_MESSAGE = 'Tu cuenta no tiene acceso a este agente.';

const MESSAGES: Record<FailureKind, string> = {
  needsContext: 'El titulo es muy corto. Agrega contexto.',
  contextTooLong: CONTEXT_TOO_LONG_MESSAGE,
  titleEmpty: TITLE_EMPTY_MESSAGE,
  titleTooLong: TITLE_TOO_LONG_MESSAGE,
  rateLimited: 'Hay demasiadas solicitudes. Espera 30 segundos e inténtalo de nuevo.',
  sessionInvalid: SESSION_EXPIRED_MESSAGE,
  accessDenied: ACCESS_DENIED_MESSAGE,
  timeout: 'La generación superó los 60 segundos. Inténtalo de nuevo.',
  failed: GENERIC_FAILURE_MESSAGE,
};

const KIND_BY_CODE: Record<string, FailureKind> = {
  NEEDS_CONTEXT: 'needsContext',
  CONTEXT_TOO_LONG: 'contextTooLong',
  TITLE_EMPTY: 'titleEmpty',
  TITLE_TOO_LONG: 'titleTooLong',
  RATE_LIMITED: 'rateLimited',
  SESSION_INVALID: 'sessionInvalid',
  ACCOUNT_NOT_ALLOWED: 'accessDenied',
};

/** Fallo del servicio ya traducido: el `message` es siempre un texto propio en español. */
export class ApiFailure extends Error {
  readonly kind: FailureKind;
  readonly retryable: boolean;

  constructor(kind: FailureKind, retryable: boolean) {
    super(MESSAGES[kind]);
    this.name = 'ApiFailure';
    this.kind = kind;
    this.retryable = retryable;
  }
}

export interface GenerateInput {
  title: string;
  context?: string;
}

export interface SessionInfo {
  accountId: string;
}

export interface ApiClient {
  generateStory(input: GenerateInput): Promise<StoryResult>;
  getSession(): Promise<SessionInfo>;
  deleteSession(): Promise<void>;
}

export interface ApiClientOptions {
  baseUrl: string;
  getToken: () => string | null;
}

async function readJson(response: Response): Promise<Record<string, unknown> | null> {
  try {
    const body: unknown = await response.json();
    return typeof body === 'object' && body !== null ? (body as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

async function toFailure(response: Response): Promise<ApiFailure> {
  const body = await readJson(response);
  const code = body?.code;
  if (typeof code !== 'string') return new ApiFailure('failed', true);
  const kind = KIND_BY_CODE[code];
  const retryable = body?.retryable !== false;
  return kind === undefined ? new ApiFailure('failed', retryable) : new ApiFailure(kind, retryable);
}

export function createApiClient({ baseUrl, getToken }: ApiClientOptions): ApiClient {
  async function call<T>(
    method: 'GET' | 'POST' | 'DELETE',
    path: string,
    body: unknown,
    parse: (response: Response) => Promise<T>,
  ): Promise<T> {
    const token = getToken();
    if (token === null) throw new ApiFailure('sessionInvalid', false);

    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const timeout = new Promise<never>((_resolve, reject) => {
      timer = setTimeout(() => {
        controller.abort();
        reject(new ApiFailure('timeout', true));
      }, API_TIMEOUT_MS);
    });

    const request = (async () => {
      let response: Response;
      try {
        response = await fetch(`${baseUrl}${path}`, {
          method,
          headers: {
            Authorization: `Bearer ${token}`,
            ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
          },
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: controller.signal,
        });
      } catch {
        throw new ApiFailure('failed', true);
      }
      if (!response.ok) throw await toFailure(response);
      return parse(response);
    })();
    // Si el temporizador gana, el resultado tardío de la solicitud se descarta sin ruido.
    request.catch(() => undefined);

    try {
      return await Promise.race([request, timeout]);
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    generateStory({ title, context }) {
      const payload = context !== undefined && context !== '' ? { title, context } : { title };
      return call('POST', '/v1/stories', payload, async (response) => {
        const body = await readJson(response);
        if (typeof body?.markdown !== 'string' || body.markdown === '') {
          throw new ApiFailure('failed', true);
        }
        const requestId = typeof body.requestId === 'string' ? body.requestId : '';
        return { requestId, markdown: body.markdown };
      });
    },

    getSession() {
      return call('GET', '/v1/session', undefined, async (response) => {
        const body = await readJson(response);
        if (typeof body?.accountId !== 'string' || body.accountId === '') {
          throw new ApiFailure('failed', true);
        }
        return { accountId: body.accountId };
      });
    },

    deleteSession() {
      return call('DELETE', '/v1/session', undefined, async () => undefined);
    },
  };
}
