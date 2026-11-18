import { ThemeProvider } from '@mui/material';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { ApiFailure } from '../api/client';
import AppThemeProvider from '../components/AppThemeProvider';
import { createAppTheme } from '../theme';
import { axe } from './axe';
import { resetStartupForTests } from '../state/useStoryScreen';
import { makeFakes, type Fakes } from './helpers';

function renderThemed(fakes: Fakes) {
  return render(
    <ThemeProvider theme={createAppTheme('light')}>
      <App services={fakes.services} />
    </ThemeProvider>,
  );
}

async function openS2(fakes: Fakes) {
  const view = renderThemed(fakes);
  await screen.findByLabelText('Titulo de la funcionalidad');
  return view;
}

function generate(title = 'Recuperar contraseña') {
  fireEvent.change(screen.getByLabelText('Titulo de la funcionalidad'), {
    target: { value: title },
  });
  return userEvent.click(screen.getByRole('button', { name: 'Generar historia' }));
}

beforeEach(() => {
  resetStartupForTests();
  sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('accesibilidad con vitest-axe (NFR6.1)', () => {
  it('S1 no tiene violaciones y declara un solo h1, header y main', async () => {
    const fakes = makeFakes({ callback: 'none' });
    const { container } = renderThemed(fakes);
    await screen.findByRole('button', { name: 'Continuar con Gmail' });

    expect(await axe(container)).toHaveNoViolations();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('S1 con el aviso de acceso no tiene violaciones', async () => {
    const fakes = makeFakes({ callback: 'error' });
    const { container } = renderThemed(fakes);
    await screen.findByRole('alert');

    expect(await axe(container)).toHaveNoViolations();
  });

  it('S2 vacío no tiene violaciones', async () => {
    const { container } = await openS2(makeFakes());

    expect(await axe(container)).toHaveNoViolations();
  });

  it('S2 cargando no tiene violaciones', async () => {
    const fakes = makeFakes();
    fakes.api.generateStory.mockReturnValue(new Promise(() => undefined));
    const { container } = await openS2(fakes);
    await generate();

    expect(await axe(container)).toHaveNoViolations();
  });

  it('S2 con error de título y con fallo del servicio no tiene violaciones', async () => {
    const fakes = makeFakes();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('failed', true));
    const { container } = await openS2(fakes);
    await generate('');
    expect(await axe(container)).toHaveNoViolations();

    await generate();
    await screen.findByRole('alert');
    expect(await axe(container)).toHaveNoViolations();
  });

  it('S2 pidiendo contexto no tiene violaciones', async () => {
    const fakes = makeFakes();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('needsContext', false));
    const { container } = await openS2(fakes);
    await generate('Login');
    await screen.findByLabelText('Contexto');

    expect(await axe(container)).toHaveNoViolations();
  });

  it('S2 con resultado no tiene violaciones en ninguna de las dos pestañas', async () => {
    const fakes = makeFakes();
    fakes.api.generateStory.mockResolvedValue({
      requestId: 'r',
      markdown: '# Historia\n\n```gherkin\nDado algo\n```',
    });
    const { container } = await openS2(fakes);
    await generate();
    await screen.findByRole('heading', { name: 'Historia' });
    expect(await axe(container)).toHaveNoViolations();

    await userEvent.click(screen.getByRole('tab', { name: 'Markdown' }));
    expect(await axe(container)).toHaveNoViolations();
  });

  it('los errores llevan icono y texto: el aviso trae un icono decorativo oculto', async () => {
    const fakes = makeFakes();
    fakes.api.generateStory.mockRejectedValue(new ApiFailure('failed', true));
    await openS2(fakes);
    await generate();

    const alert = await screen.findByRole('alert');
    expect(alert.querySelector('svg[aria-hidden="true"]')).not.toBeNull();
    expect(alert.textContent).toMatch(/No se pudo generar/);
  });
});

describe('tema (BR5.9, NFR7.1)', () => {
  it('define un tamaño táctil mínimo de 44 px en botones, pestañas, iconos y campos', () => {
    const components = createAppTheme('light').components as Record<
      string,
      { styleOverrides?: { root?: Record<string, unknown> } }
    >;

    for (const name of ['MuiButton', 'MuiTab', 'MuiIconButton']) {
      expect(components[name].styleOverrides?.root).toMatchObject({ minHeight: 44, minWidth: 44 });
    }
    expect(components.MuiOutlinedInput.styleOverrides?.root).toMatchObject({ minHeight: 44 });
  });

  it('tiene un tema claro y uno oscuro con la paleta por defecto', () => {
    expect(createAppTheme('light').palette.mode).toBe('light');
    expect(createAppTheme('dark').palette.mode).toBe('dark');
  });

  it.each([
    [true, 'dark'],
    [false, 'light'],
  ])('AppThemeProvider sigue la preferencia del sistema (oscuro=%s)', async (dark, expected) => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('prefers-color-scheme: dark') ? dark : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      })),
    );
    render(
      <AppThemeProvider>
        <p>contenido</p>
      </AppThemeProvider>,
    );

    await waitFor(() => expect(document.documentElement.dataset.themeMode).toBe(expected));
    expect(screen.getByText('contenido')).toBeVisible();
  });
});
