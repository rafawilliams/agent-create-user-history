/** Estado único de la pantalla principal (ENT-002, BR5.2 a BR5.7) y sus transiciones. */

export type ScreenKind =
  | 'signedOut'
  | 'signingIn'
  | 'idle'
  | 'needsContext'
  | 'generating'
  | 'result'
  | 'failed'
  | 'sessionExpired'
  | 'accessDenied';

export interface StoryResult {
  requestId: string;
  markdown: string;
}

export interface Failure {
  message: string;
  retryable: boolean;
  /** Qué repite "Reintentar": la generación o la comprobación de la sesión. */
  retry: 'generate' | 'session';
  /** Marca de tiempo (ms) hasta la que "Reintentar" queda desactivado (límite de tasa). */
  blockedUntil: number | null;
}

export interface ScreenState {
  kind: ScreenKind;
  /** S1: muestra "No se pudo iniciar sesión". */
  authError: boolean;
  titleError: string | null;
  /** Mensaje bajo el título cuando el servicio pide contexto. */
  contextMessage: string | null;
  contextError: string | null;
  failure: Failure | null;
  result: StoryResult | null;
  /** Aviso informativo (por ejemplo, copia descartada por cambio de cuenta). */
  notice: string | null;
}

export type Action =
  | { type: 'signInStarted' }
  | { type: 'signInFailed' }
  | { type: 'sessionConfirmed'; needsContext?: boolean; notice?: string | null }
  | { type: 'sessionCheckFailed'; message: string }
  | { type: 'submitted' }
  | { type: 'validationFailed'; field: 'title' | 'context'; message: string }
  | { type: 'generated'; result: StoryResult }
  | { type: 'needsContext'; message?: string; contextError?: string }
  | { type: 'titleRejected'; message: string }
  | { type: 'failed'; message: string; retryable: boolean; blockedUntil?: number | null }
  | { type: 'edited' }
  | { type: 'sessionExpired' }
  | { type: 'accessDenied' }
  | { type: 'signedOut' };

export function initialState(callbackPending = false): ScreenState {
  return {
    kind: callbackPending ? 'signingIn' : 'signedOut',
    authError: false,
    titleError: null,
    contextMessage: null,
    contextError: null,
    failure: null,
    result: null,
    notice: null,
  };
}

const SUBMITTABLE: ScreenKind[] = ['idle', 'needsContext', 'failed', 'result'];
const WITH_SESSION: ScreenKind[] = [...SUBMITTABLE, 'generating'];

export function reduce(state: ScreenState, action: Action): ScreenState {
  switch (action.type) {
    case 'signInStarted':
      return { ...initialState(), kind: 'signingIn' };
    case 'signInFailed':
      return { ...initialState(), authError: true };
    case 'signedOut':
      return initialState();
    case 'sessionConfirmed':
      return {
        ...initialState(),
        kind: action.needsContext ? 'needsContext' : 'idle',
        notice: action.notice ?? null,
      };
    case 'sessionCheckFailed':
      return {
        ...initialState(),
        kind: 'failed',
        failure: { message: action.message, retryable: true, retry: 'session', blockedUntil: null },
      };
    case 'submitted':
      if (!SUBMITTABLE.includes(state.kind)) return state;
      return {
        ...state,
        kind: 'generating',
        failure: null,
        result: null,
        titleError: null,
        contextError: null,
        notice: null,
      };
    case 'validationFailed':
      if (!SUBMITTABLE.includes(state.kind)) return state;
      return action.field === 'title'
        ? { ...state, titleError: action.message }
        : { ...state, contextError: action.message };
    case 'generated':
      if (state.kind !== 'generating') return state;
      return { ...state, kind: 'result', result: action.result, failure: null };
    case 'needsContext':
      if (state.kind !== 'generating') return state;
      return {
        ...state,
        kind: 'needsContext',
        contextMessage: action.message ?? state.contextMessage,
        contextError: action.contextError ?? null,
        result: null,
      };
    case 'titleRejected':
      if (state.kind !== 'generating') return state;
      return { ...state, kind: 'idle', titleError: action.message };
    case 'failed':
      if (state.kind !== 'generating') return state;
      return {
        ...state,
        kind: 'failed',
        failure: {
          message: action.message,
          retryable: action.retryable,
          retry: 'generate',
          blockedUntil: action.blockedUntil ?? null,
        },
      };
    case 'edited': {
      const cleared = { ...state, titleError: null, contextError: null };
      if (
        state.kind === 'failed' &&
        state.failure?.retry === 'generate' &&
        !state.failure.retryable
      ) {
        return { ...cleared, kind: 'idle', failure: null };
      }
      return cleared;
    }
    case 'sessionExpired':
      if (!WITH_SESSION.includes(state.kind)) return state;
      return { ...initialState(), kind: 'sessionExpired' };
    case 'accessDenied':
      return { ...initialState(), kind: 'accessDenied' };
  }
}
