/**
 * Controlador de la pantalla: une el estado (ENT-002), la validación, el cliente del servicio,
 * el token en memoria y la copia temporal. Los componentes solo pintan lo que este hook entrega.
 */
import { useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { ApiFailure, GENERIC_FAILURE_MESSAGE } from '../api/client';
import type { Provider } from '../auth/authClient';
import { clearDraft, restoreDraft, saveDraft, type Draft } from '../draft/draftStore';
import type { Services } from '../services';
import { validateContext, validateTitle } from '../validation';
import { initialState, reduce, type ScreenState } from './screenState';

/** Tiempo que "Reintentar" queda desactivado tras un 429 (BR5.4). */
export const RATE_LIMIT_BLOCK_MS = 30_000;
export const DISCARDED_NOTICE =
  'Se descartó lo que habías escrito porque iniciaste sesión con otra cuenta.';

type StartupOutcome =
  | { kind: 'none' }
  | { kind: 'authError' }
  | { kind: 'ready'; accountId: string; draft: Draft | null; discarded: boolean }
  | { kind: 'accessDenied' }
  | { kind: 'sessionExpired' }
  | { kind: 'checkFailed' };

/** Comprueba la sesión (C2) y, si es válida, restaura la copia temporal de la misma cuenta. */
async function confirmSession(services: Services): Promise<StartupOutcome> {
  try {
    const { accountId } = await services.api.getSession();
    const restored = restoreDraft(accountId);
    return {
      kind: 'ready',
      accountId,
      draft: restored.status === 'restored' ? restored.draft : null,
      discarded: restored.status === 'discarded',
    };
  } catch (error) {
    if (error instanceof ApiFailure && error.kind === 'accessDenied') {
      clearDraft();
      return { kind: 'accessDenied' };
    }
    if (error instanceof ApiFailure && error.kind === 'sessionInvalid') {
      return { kind: 'sessionExpired' };
    }
    return { kind: 'checkFailed' };
  }
}

// El arranque (retorno del acceso y comprobación de la sesión) corre una sola vez por carga de
// página, aunque StrictMode ejecute el efecto dos veces.
let startupPromise: Promise<StartupOutcome> | null = null;

export function resetStartupForTests(): void {
  startupPromise = null;
}

if (import.meta.hot) {
  import.meta.hot.dispose(resetStartupForTests);
}

function runStartup(services: Services): Promise<StartupOutcome> {
  startupPromise ??= services.auth.consumeCallback().then(async (callback) => {
    if (callback.status === 'none') return { kind: 'none' } as const;
    if (callback.status === 'error') {
      clearDraft();
      return { kind: 'authError' } as const;
    }
    return confirmSession(services);
  });
  return startupPromise;
}

export interface StoryScreen {
  state: ScreenState;
  title: string;
  context: string;
  /** El campo de contexto está a la vista (el servicio lo pidió). */
  showContext: boolean;
  /** Contadores que suben cada vez que un campo debe recibir el foco. */
  focus: { title: number; context: number };
  setTitle(value: string): void;
  setContext(value: string): void;
  signIn(provider: Provider): void;
  submit(): void;
  retry(): void;
  logout(): void;
  restartSignIn(): void;
}

export function useStoryScreen(services: Services): StoryScreen {
  const { auth, api, holder } = services;
  const [state, dispatch] = useReducer(reduce, undefined, () =>
    initialState(auth.callbackPending()),
  );
  const [title, setTitleValue] = useState('');
  const [context, setContextValue] = useState('');
  const [contextRequested, setContextRequested] = useState(false);
  const [focus, setFocus] = useState({ title: 0, context: 0 });
  const accountId = useRef<string | null>(null);
  const inFlight = useRef(false);
  const requestSeq = useRef(0);

  const showContext =
    state.kind === 'needsContext' ||
    (contextRequested && (state.kind === 'generating' || state.kind === 'failed'));

  const bumpFocus = useCallback((field: 'title' | 'context') => {
    setFocus((current) => ({ ...current, [field]: current[field] + 1 }));
  }, []);

  const applyOutcome = useCallback(
    (outcome: StartupOutcome) => {
      switch (outcome.kind) {
        case 'none':
          return;
        case 'authError':
          dispatch({ type: 'signInFailed' });
          return;
        case 'ready': {
          accountId.current = outcome.accountId;
          const withContext = outcome.draft !== null && outcome.draft.context !== '';
          if (outcome.draft !== null) {
            setTitleValue(outcome.draft.title);
            setContextValue(outcome.draft.context);
          }
          setContextRequested(withContext);
          dispatch({
            type: 'sessionConfirmed',
            needsContext: withContext,
            notice: outcome.discarded ? DISCARDED_NOTICE : null,
          });
          return;
        }
        case 'accessDenied':
          dispatch({ type: 'accessDenied' });
          return;
        case 'sessionExpired':
          void auth.dropSession();
          dispatch({ type: 'sessionExpired' });
          return;
        case 'checkFailed':
          dispatch({ type: 'sessionCheckFailed', message: GENERIC_FAILURE_MESSAGE });
          return;
      }
    },
    [auth],
  );

  useEffect(() => {
    void runStartup(services).then(applyOutcome);
    // El arranque corre una vez por carga de página: las dependencias no cambian durante la vida de la pantalla.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const expire = useCallback(async () => {
    if (accountId.current !== null) {
      saveDraft({ title, context, accountId: accountId.current });
    }
    await auth.dropSession();
    dispatch({ type: 'sessionExpired' });
  }, [auth, title, context]);

  const handleFailure = useCallback(
    async (error: unknown) => {
      const failure = error instanceof ApiFailure ? error : new ApiFailure('failed', true);
      switch (failure.kind) {
        case 'needsContext':
          setContextRequested(true);
          dispatch({ type: 'needsContext', message: failure.message });
          bumpFocus('context');
          return;
        case 'contextTooLong':
          setContextRequested(true);
          dispatch({ type: 'needsContext', contextError: failure.message });
          bumpFocus('context');
          return;
        case 'titleEmpty':
        case 'titleTooLong':
          dispatch({ type: 'titleRejected', message: failure.message });
          bumpFocus('title');
          return;
        case 'sessionInvalid':
          await expire();
          return;
        case 'accessDenied':
          clearDraft();
          dispatch({ type: 'accessDenied' });
          return;
        case 'rateLimited':
          dispatch({
            type: 'failed',
            message: failure.message,
            retryable: failure.retryable,
            blockedUntil: Date.now() + RATE_LIMIT_BLOCK_MS,
          });
          return;
        default:
          dispatch({ type: 'failed', message: failure.message, retryable: failure.retryable });
      }
    },
    [bumpFocus, expire],
  );

  const submit = useCallback(async () => {
    if (inFlight.current) return;

    const validTitle = validateTitle(title);
    if (!validTitle.ok) {
      dispatch({ type: 'validationFailed', field: 'title', message: validTitle.message });
      bumpFocus('title');
      return;
    }
    let contextValue: string | undefined;
    if (showContext) {
      const validContext = validateContext(context);
      if (!validContext.ok) {
        dispatch({ type: 'validationFailed', field: 'context', message: validContext.message });
        bumpFocus('context');
        return;
      }
      contextValue = validContext.value;
    }
    if (holder.getToken() === null) {
      await expire();
      return;
    }

    // Un solo envío a la vez: la referencia se fija antes de cualquier espera y el estado
    // generating se despacha en el mismo manejador del clic (BR5.2, NFR1.2).
    inFlight.current = true;
    requestSeq.current += 1;
    const sequence = requestSeq.current;
    dispatch({ type: 'submitted' });
    try {
      const result = await api.generateStory(
        contextValue === undefined
          ? { title: validTitle.value }
          : { title: validTitle.value, context: contextValue },
      );
      if (sequence !== requestSeq.current) return;
      if (holder.getToken() === null) {
        await expire();
        return;
      }
      setContextRequested(false);
      dispatch({ type: 'generated', result });
    } catch (error) {
      if (sequence !== requestSeq.current) return;
      await handleFailure(error);
    } finally {
      inFlight.current = false;
    }
  }, [api, holder, title, context, showContext, bumpFocus, expire, handleFailure]);

  const retrySession = useCallback(async () => {
    dispatch({ type: 'signInStarted' });
    applyOutcome(await confirmSession(services));
  }, [services, applyOutcome]);

  return {
    state,
    title,
    context,
    showContext,
    focus,
    setTitle(value) {
      setTitleValue(value);
      dispatch({ type: 'edited' });
    },
    setContext(value) {
      setContextValue(value);
      dispatch({ type: 'edited' });
    },
    signIn(provider) {
      dispatch({ type: 'signInStarted' });
      auth.signIn(provider).catch(() => {
        clearDraft();
        dispatch({ type: 'signInFailed' });
      });
    },
    submit() {
      void submit();
    },
    retry() {
      if (state.failure?.retry === 'session') void retrySession();
      else void submit();
    },
    logout() {
      requestSeq.current += 1;
      accountId.current = null;
      setTitleValue('');
      setContextValue('');
      setContextRequested(false);
      dispatch({ type: 'signedOut' });
      void auth.signOut(() => api.deleteSession());
    },
    restartSignIn() {
      dispatch({ type: 'signedOut' });
    },
  };
}
