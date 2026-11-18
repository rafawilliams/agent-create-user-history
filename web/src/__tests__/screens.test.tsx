import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { ApiFailure } from '../api/client';
import { DRAFT_KEY, saveDraft } from '../draft/draftStore';
import { resetStartupForTests } from '../state/useStoryScreen';
import { TOKEN, makeFakes, type Fakes } from './helpers';

const OK = { requestId: 'r-1', markdown: '# Historia\n\nComo analista quiero algo' };

function renderApp(fakes: Fakes) {
  return render(<App services={fakes.services} />);
}

async function openS2(fakes: Fakes = makeFakes()) {
  const view = renderApp(fakes);
  await screen.findByLabelText('Titulo de la funcionalidad');
  return { fakes, ...view };
}

function titleInput() {
  return screen.getByLabelText('Titulo de la funcionalidad') as HTMLInputElement;
}

function setTitle(value: string) {
  fireEvent.change(titleInput(), { target: { value } });
}

beforeEach(() => {
  resetStartupForTests();
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('S1: acceso (BR5.7; AC6.1.1 a AC6.1.3)', () => {
  it('sin token solo se ve S1, sin campos y sin redirigir por sí sola', async () => {
    const fakes = makeFakes({ callback: 'none' });
    renderApp(fakes);

    expect(await screen.findByRole('button', { name: 'Continuar con Gmail' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Continuar con Outlook' })).toBeVisible();
    expect(screen.queryByLabelText('Titulo de la funcionalidad')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Cerrar sesion' })).toBeNull();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Agente analista de negocio',
    );
    expect(fakes.auth.signIn).not.toHaveBeenCalled();
  });

  it.each([
    ['Continuar con Gmail', 'Google'],
    ['Continuar con Outlook', 'Microsoft'],
  ])(
    '"%s" inicia el flujo con el proveedor %s y muestra "Iniciando sesión"',
    async (label, name) => {
      const fakes = makeFakes({ callback: 'none' });
      fakes.auth.signIn.mockReturnValue(new Promise(() => undefined));
      renderApp(fakes);

      await userEvent.click(await screen.findByRole('button', { name: label }));

      expect(fakes.auth.signIn).toHaveBeenCalledWith(name);
      expect(screen.getByRole('status')).toHaveTextContent('Iniciando sesión');
    },
  );

  it('si el proveedor falla muestra el aviso con role="alert", borra la copia y deja los botones', async () => {
    const fakes = makeFakes({ callback: 'none' });
    fakes.auth.signIn.mockRejectedValue(new Error('proveedor caído'));
    saveDraft({ title: 't', context: '', accountId: 'acc-1' });
    renderApp(fakes);

    await userEvent.click(await screen.findByRole('button', { name: 'Continuar con Gmail' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo iniciar sesión. Inténtalo de nuevo.',
    );
    expect(screen.getByRole('button', { name: 'Continuar con Gmail' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Continuar con Outlook' })).toBeEnabled();
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('un retorno con error (estado distinto o cancelación) muestra el aviso y borra la copia', async () => {
    const fakes = makeFakes({ callback: 'error' });
    saveDraft({ title: 't', context: '', accountId: 'acc-1' });
    renderApp(fakes);

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión');
    expect(fakes.api.getSession).not.toHaveBeenCalled();
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('mientras vuelve la respuesta se ve "Iniciando sesión" y luego S2', async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => (release = resolve));
    const fakes = makeFakes({ callbackGate: gate });
    renderApp(fakes);

    expect(screen.getByRole('status')).toHaveTextContent('Iniciando sesión');
    release();

    expect(await screen.findByLabelText('Titulo de la funcionalidad')).toBeVisible();
    expect(fakes.api.getSession).toHaveBeenCalledTimes(1);
  });

  it('el doble efecto de StrictMode comprueba la sesión una sola vez', async () => {
    const fakes = makeFakes();
    render(
      <StrictMode>
        <App services={fakes.services} />
      </StrictMode>,
    );

    await screen.findByLabelText('Titulo de la funcionalidad');

    expect(fakes.api.getSession).toHaveBeenCalledTimes(1);
  });

  it('ACCOUNT_NOT_ALLOWED al comprobar la sesión pasa a accessDenied con "Cerrar sesión"', async () => {
    const fakes = makeFakes();
    fakes.api.getSession.mockRejectedValue(new ApiFailure('accessDenied', false));
    saveDraft({ title: 't', context: '', accountId: 'acc-1' });
    renderApp(fakes);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Tu cuenta no tiene acceso a este agente.',
    );
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
    expect(screen.queryByLabelText('Titulo de la funcionalidad')).toBeNull();

    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }));
    expect(fakes.auth.signOut).toHaveBeenCalledTimes(1);
  });

  it('un fallo de red al comprobar la sesión ofrece reintentar la comprobación', async () => {
    const fakes = makeFakes();
    fakes.api.getSession.mockRejectedValueOnce(new ApiFailure('failed', true));
    renderApp(fakes);

    await userEvent.click(await screen.findByRole('button', { name: 'Reintentar' }));

    expect(await screen.findByLabelText('Titulo de la funcionalidad')).toBeVisible();
    expect(fakes.api.getSession).toHaveBeenCalledTimes(2);
  });
});

describe('S2: título, contador y validación (BR5.1; AC1.1.1 a AC1.1.3)', () => {
  it('el contador "N / 200" se actualiza al escribir', async () => {
    await openS2();

    expect(screen.getByText('0 / 200')).toBeVisible();
    await userEvent.type(titleInput(), 'Login');

    expect(screen.getByText('5 / 200')).toBeVisible();
  });

  it.each(['', '    '])(
    'título vacío o solo espacios (%j): mensaje y foco al campo',
    async (value) => {
      const { fakes } = await openS2();
      setTitle(value);

      await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

      expect(screen.getByText('Escribe un titulo para generar la historia.')).toBeVisible();
      expect(titleInput()).toHaveFocus();
      expect(titleInput()).toHaveAccessibleDescription(/Escribe un titulo/);
      expect(fakes.api.generateStory).not.toHaveBeenCalled();
    },
  );

  it('201 caracteres no se envían y 200 exactos sí', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockResolvedValue(OK);

    setTitle('a'.repeat(201));
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    expect(screen.getByText('El titulo no puede superar 200 caracteres.')).toBeVisible();
    expect(fakes.api.generateStory).not.toHaveBeenCalled();

    setTitle('a'.repeat(200));
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    await waitFor(() => expect(fakes.api.generateStory).toHaveBeenCalledTimes(1));
    expect(fakes.api.generateStory).toHaveBeenCalledWith({ title: 'a'.repeat(200) });
  });

  it('Enter en el campo envía el formulario con el título recortado', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockResolvedValue(OK);

    await userEvent.type(titleInput(), '  Recuperar contraseña  {Enter}');

    await waitFor(() =>
      expect(fakes.api.generateStory).toHaveBeenCalledWith({ title: 'Recuperar contraseña' }),
    );
  });
});

describe('S2: generación, carga y un solo envío (BR5.2; AC5.1.1)', () => {
  it('el indicador y el bloqueo aparecen en el mismo ciclo del clic y no depende de la respuesta', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockReturnValue(new Promise(() => undefined));
    setTitle('Recuperar contraseña');

    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(screen.getByRole('status')).toHaveTextContent('Generando la historia');
    expect(screen.getByRole('button', { name: 'Generar historia' })).toBeDisabled();
    expect(titleInput()).toBeDisabled();
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('un doble clic envía una sola solicitud', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockReturnValue(new Promise(() => undefined));
    setTitle('Recuperar contraseña');

    await userEvent.dblClick(screen.getByRole('button', { name: 'Generar historia' }));

    expect(fakes.api.generateStory).toHaveBeenCalledTimes(1);
  });

  it('con éxito muestra el resultado y vuelve a habilitar los controles', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockResolvedValue(OK);
    setTitle('Recuperar contraseña');

    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByRole('tab', { name: 'Vista previa' })).toBeVisible();
    expect(titleInput()).toBeEnabled();
    expect(screen.queryByRole('status', { name: /Generando/ })).toBeNull();
  });
});

describe('S2: contexto (BR5.3; AC1.1.4)', () => {
  async function toNeedsContext() {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValueOnce(new ApiFailure('needsContext', false));
    setTitle('Login');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    await screen.findByLabelText('Contexto');
    return fakes;
  }

  it('NEEDS_CONTEXT muestra el mensaje bajo el título, enfoca el contexto y no muestra historia', async () => {
    await toNeedsContext();

    expect(screen.getByText('El titulo es muy corto. Agrega contexto.')).toBeVisible();
    expect(screen.getByLabelText('Contexto')).toHaveFocus();
    expect(screen.queryByRole('tab')).toBeNull();
  });

  it('contexto vacío o de más de 500 caracteres no se envía y muestra su mensaje', async () => {
    const fakes = await toNeedsContext();
    fakes.api.generateStory.mockClear();

    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    expect(screen.getByText('Agrega contexto para generar la historia.')).toBeVisible();

    fireEvent.change(screen.getByLabelText('Contexto'), { target: { value: 'x'.repeat(501) } });
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    expect(screen.getByText('El contexto no puede superar 500 caracteres.')).toBeVisible();
    expect(fakes.api.generateStory).not.toHaveBeenCalled();
  });

  it('con contexto válido envía título y contexto', async () => {
    const fakes = await toNeedsContext();
    fakes.api.generateStory.mockResolvedValue(OK);

    fireEvent.change(screen.getByLabelText('Contexto'), { target: { value: '  Para admins  ' } });
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    await waitFor(() =>
      expect(fakes.api.generateStory).toHaveBeenCalledWith({
        title: 'Login',
        context: 'Para admins',
      }),
    );
    expect(await screen.findByRole('tab', { name: 'Vista previa' })).toBeVisible();
  });

  it('CONTEXT_TOO_LONG del servicio deja el error en el campo de contexto', async () => {
    const fakes = await toNeedsContext();
    fakes.api.generateStory.mockRejectedValueOnce(new ApiFailure('contextTooLong', false));

    fireEvent.change(screen.getByLabelText('Contexto'), { target: { value: 'algo' } });
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByText('El contexto no puede superar 500 caracteres.')).toBeVisible();
  });
});

describe('S2: fallos y reintento (BR5.4; AC5.1.2, AC5.1.3)', () => {
  it('un fallo muestra el mensaje propio con role="alert" y "Reintentar" conserva el título', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValueOnce(new ApiFailure('failed', true));
    setTitle('Recuperar contraseña');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('No se pudo generar la historia. Inténtalo de nuevo.');
    expect(titleInput()).toHaveValue('Recuperar contraseña');
    const retry = within(alert).getByRole('button', { name: 'Reintentar' });
    expect(retry).toHaveFocus();

    fakes.api.generateStory.mockResolvedValueOnce(OK);
    await userEvent.click(retry);

    expect(await screen.findByRole('tab', { name: 'Vista previa' })).toBeVisible();
    expect(fakes.api.generateStory).toHaveBeenLastCalledWith({ title: 'Recuperar contraseña' });
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('el corte de 60 s muestra su mensaje con "Reintentar"', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('timeout', true));
    setTitle('Algo');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La generación superó los 60 segundos. Inténtalo de nuevo.',
    );
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeEnabled();
  });

  it('RATE_LIMITED deja "Reintentar" desactivado 30 segundos', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('rateLimited', true));
    setTitle('Algo');
    fireEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Espera 30 segundos');
    const retry = screen.getByRole('button', { name: 'Reintentar' });
    expect(retry).toBeDisabled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(29_000);
    });
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDisabled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeEnabled();
  });

  it('un fallo no reintentable no ofrece "Reintentar" y "Generar historia" sigue disponible', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('failed', false));
    setTitle('Algo');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByRole('alert')).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Generar historia' })).toBeEnabled();
  });

  it('TITLE_TOO_LONG del servicio deja el mensaje del título', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('titleTooLong', false));
    setTitle('Algo');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByText('El titulo no puede superar 200 caracteres.')).toBeVisible();
    expect(titleInput()).toHaveFocus();
  });
});

describe('sesión vencida y copia temporal (BR5.6, NFR4.4; AC6.1.2)', () => {
  it('SESSION_INVALID pasa a sessionExpired, guarda la copia y olvida el token', async () => {
    const { fakes } = await openS2();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('sessionInvalid', false));
    setTitle('Recuperar contraseña');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Tu sesión terminó. Inicia sesión de nuevo para continuar.',
    );
    expect(JSON.parse(sessionStorage.getItem(DRAFT_KEY) as string)).toEqual({
      title: 'Recuperar contraseña',
      context: '',
      accountId: 'acc-1',
    });
    expect(fakes.auth.dropSession).toHaveBeenCalled();
    expect(sessionStorage.getItem(DRAFT_KEY)).not.toContain(TOKEN);

    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión de nuevo' }));
    expect(screen.getByRole('button', { name: 'Continuar con Gmail' })).toBeVisible();
  });

  it('un token vencido al pulsar "Generar historia" no llama al servicio', async () => {
    const { fakes } = await openS2();
    setTitle('Algo');
    fakes.clock.now = 2_000_001;

    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    expect(fakes.api.generateStory).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent('Tu sesión terminó');
    expect(JSON.parse(sessionStorage.getItem(DRAFT_KEY) as string).title).toBe('Algo');
  });

  it('el resultado que llega con la sesión ya vencida se descarta', async () => {
    const { fakes } = await openS2();
    let resolve!: (value: typeof OK) => void;
    fakes.api.generateStory.mockReturnValue(new Promise((r) => (resolve = r)));
    setTitle('Algo');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));

    fakes.clock.now = 2_000_001;
    await act(async () => resolve(OK));

    expect(await screen.findByRole('alert')).toHaveTextContent('Tu sesión terminó');
    expect(screen.queryByRole('tab')).toBeNull();
  });

  it('al volver con la misma cuenta restaura el título y borra la copia', async () => {
    saveDraft({ title: 'Recuperar contraseña', context: '', accountId: 'acc-1' });

    await openS2();

    expect(titleInput()).toHaveValue('Recuperar contraseña');
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it('si había contexto vuelve a needsContext con el contexto restaurado', async () => {
    saveDraft({ title: 'Login', context: 'Para admins', accountId: 'acc-1' });

    renderApp(makeFakes());

    expect(await screen.findByLabelText('Contexto')).toHaveValue('Para admins');
    expect(titleInput()).toHaveValue('Login');
  });

  it('con otra cuenta descarta lo guardado y lo avisa', async () => {
    saveDraft({ title: 'Ajeno', context: '', accountId: 'acc-OTRA' });

    await openS2();

    expect(titleInput()).toHaveValue('');
    expect(screen.getByText(/Se descartó lo que habías escrito/)).toBeVisible();
    expect(sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });
});

describe('cierre de sesión (BR5.8; AC6.1.1)', () => {
  it('"Cerrar sesion" llama a DELETE por medio del cierre y no deja resultado en curso', async () => {
    const { fakes } = await openS2();

    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesion' }));

    expect(fakes.auth.signOut).toHaveBeenCalledTimes(1);
    expect(fakes.api.deleteSession).toHaveBeenCalledTimes(1);
  });

  it('en móvil "Cerrar sesion" está dentro de un menú del encabezado', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: true,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      })),
    );
    const { fakes } = await openS2();

    expect(screen.queryByRole('button', { name: 'Cerrar sesion' })).toBeNull();
    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }));
    await userEvent.click(await screen.findByRole('menuitem', { name: 'Cerrar sesion' }));

    expect(fakes.auth.signOut).toHaveBeenCalledTimes(1);
  });
});

describe('privacidad en la consola (NFR4.2)', () => {
  it('ni el token, ni el título, ni el contexto, ni el Markdown llegan a console.*', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((method) =>
      vi.spyOn(console, method).mockImplementation(() => undefined),
    );
    const { fakes } = await openS2();
    fakes.api.generateStory
      .mockRejectedValueOnce(new ApiFailure('needsContext', false))
      .mockRejectedValueOnce(new ApiFailure('failed', true))
      .mockResolvedValueOnce({ requestId: 'r', markdown: '# MARKDOWN-SECRETO' });

    setTitle('TITULO-SECRETO');
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    fireEvent.change(await screen.findByLabelText('Contexto'), {
      target: { value: 'CONTEXTO-SECRETO' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Reintentar' }));
    await screen.findByRole('tab', { name: 'Vista previa' });

    const logged = spies.flatMap((spy) => spy.mock.calls).map((args) => JSON.stringify(args));
    for (const secret of [TOKEN, 'TITULO-SECRETO', 'CONTEXTO-SECRETO', 'MARKDOWN-SECRETO']) {
      expect(logged.join('\n')).not.toContain(secret);
    }
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(TOKEN);
    vi.restoreAllMocks();
  });
});
