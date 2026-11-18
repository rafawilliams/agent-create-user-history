import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ResultView from '../components/ResultView';

const MARKDOWN = [
  '# Historia de usuario',
  '',
  'Como analista quiero **recuperar** mi contraseña',
  '',
  '```gherkin',
  'Dado que olvidé mi contraseña',
  'Cuando pido el enlace',
  'Entonces recibo un correo',
  '```',
].join('\n');

const HOSTILE = [
  '# Título',
  '<script>window.__pwned = 1</script>',
  '<img src="https://evil.example/pixel.png" onerror="window.__pwned = 2">',
  '<a href="javascript:window.__pwned=3" onclick="window.__pwned=4">html</a>',
  '[js](javascript:window.__pwned=5)',
  '[datos](data:text/html;base64,PHNjcmlwdD4=)',
  '[ftp](ftp://archivos.example/a)',
  '![logo remoto](https://evil.example/logo.png)',
  '[web](http://sitio.example/a) [seguro](https://sitio.example/b) [correo](mailto:a@b.example)',
].join('\n\n');

const writeText = vi.fn();
const fetchMock = vi.fn();

beforeEach(() => {
  writeText.mockReset();
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  delete (window as unknown as Record<string, unknown>).__pwned;
});

async function renderResult(markdown = MARKDOWN, loader?: () => Promise<{ default: never }>) {
  const view = render(<ResultView markdown={markdown} previewLoader={loader as never} />);
  return view;
}

describe('ResultView: pestañas (BR5.5; AC4.1.1)', () => {
  it('muestra "Vista previa" y "Markdown" con el mismo contenido', async () => {
    await renderResult();

    const tabs = screen.getAllByRole('tab');
    expect(tabs.map((tab) => tab.textContent)).toEqual(['Vista previa', 'Markdown']);
    expect(screen.getByRole('tab', { name: 'Vista previa' })).toHaveAttribute(
      'aria-selected',
      'true',
    );

    const panel = await screen.findByRole('tabpanel');
    expect(
      await within(panel).findByRole('heading', { name: 'Historia de usuario' }),
    ).toBeVisible();
    expect(panel.querySelector('pre code')?.textContent).toContain('Dado que olvidé mi contraseña');

    await userEvent.click(screen.getByRole('tab', { name: 'Markdown' }));
    expect(screen.getByRole('tabpanel').textContent).toBe(MARKDOWN);
  });

  it('las flechas del teclado cambian de pestaña', async () => {
    await renderResult();

    screen.getByRole('tab', { name: 'Vista previa' }).focus();
    await userEvent.keyboard('{ArrowRight}');
    expect(screen.getByRole('tab', { name: 'Markdown' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'Markdown' })).toHaveFocus();

    await userEvent.keyboard('{ArrowLeft}');
    expect(screen.getByRole('tab', { name: 'Vista previa' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });

  it('el texto Markdown es seleccionable (un bloque de texto, no una imagen)', async () => {
    await renderResult();
    await userEvent.click(screen.getByRole('tab', { name: 'Markdown' }));

    expect(screen.getByRole('tabpanel').querySelector('pre')).not.toBeNull();
  });

  it('mientras la vista previa se descarga muestra "Cargando vista previa"', async () => {
    await renderResult(MARKDOWN, () => new Promise(() => undefined));

    expect(await screen.findByText('Cargando vista previa')).toBeVisible();
  });
});

describe('ResultView: copiado (BR5.5; AC4.1.2, AC4.1.3)', () => {
  it('copia exactamente el Markdown recibido y confirma en una región de estado', async () => {
    writeText.mockResolvedValue(undefined);
    await renderResult();

    await userEvent.click(screen.getByRole('button', { name: 'Copiar Markdown' }));

    expect(writeText).toHaveBeenCalledWith(MARKDOWN);
    expect(await screen.findByRole('status')).toHaveTextContent('Markdown copiado');
  });

  it('si el navegador rechaza la copia avisa de que hay que copiar a mano', async () => {
    writeText.mockRejectedValue(new Error('NotAllowedError'));
    await renderResult();

    await userEvent.click(screen.getByRole('button', { name: 'Copiar Markdown' }));

    expect(await screen.findByRole('status')).toHaveTextContent(
      'No se pudo copiar. Selecciona el texto y cópialo a mano.',
    );
    expect(screen.queryByText('Markdown copiado')).toBeNull();
  });

  it('sin portapapeles disponible también avisa', async () => {
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
    await renderResult();

    await userEvent.click(screen.getByRole('button', { name: 'Copiar Markdown' }));

    expect(await screen.findByRole('status')).toHaveTextContent('No se pudo copiar');
  });
});

describe('MarkdownPreview: nunca ejecuta HTML (NFR4.3)', () => {
  it('no deja scripts, controladores de evento, enlaces javascript: ni imágenes remotas', async () => {
    const { container } = await renderResult(HOSTILE);
    const panel = await screen.findByRole('tabpanel');
    await within(panel).findByRole('heading', { name: 'Título' });

    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('[onerror], [onclick]')).toBeNull();
    expect(container.querySelector('a[href^="javascript:"]')).toBeNull();
    expect(container.querySelector('a[href^="data:"]')).toBeNull();
    expect(container.querySelector('a[href^="ftp:"]')).toBeNull();
    expect((window as unknown as Record<string, unknown>).__pwned).toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('las imágenes se muestran como texto y los enlaces sin esquema permitido pierden el href', async () => {
    await renderResult(HOSTILE);
    const panel = await screen.findByRole('tabpanel');
    await within(panel).findByRole('heading', { name: 'Título' });

    expect(panel).toHaveTextContent('logo remoto');
    for (const name of ['js', 'datos', 'ftp']) {
      const link = within(panel).getByText(name);
      expect(link.closest('a')?.hasAttribute('href') ?? false).toBe(false);
    }
  });

  it('solo http, https y mailto se enlazan, con rel="noopener noreferrer" y en otra pestaña', async () => {
    await renderResult(HOSTILE);
    const panel = await screen.findByRole('tabpanel');
    await within(panel).findByRole('heading', { name: 'Título' });

    for (const [name, href] of [
      ['web', 'http://sitio.example/a'],
      ['seguro', 'https://sitio.example/b'],
      ['correo', 'mailto:a@b.example'],
    ]) {
      const link = within(panel).getByRole('link', { name });
      expect(link).toHaveAttribute('href', href);
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveAttribute('target', '_blank');
    }
  });
});

describe('ResultView: falla la carga diferida (NFR1.3)', () => {
  it('avisa, y la pestaña Markdown y el botón de copiar siguen funcionando', async () => {
    writeText.mockResolvedValue(undefined);
    const loader = vi.fn().mockRejectedValue(new Error('chunk perdido'));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    await renderResult(MARKDOWN, loader);

    expect(
      await screen.findByText('No se pudo cargar la vista previa. Usa la pestaña Markdown.'),
    ).toBeVisible();

    await userEvent.click(screen.getByRole('tab', { name: 'Markdown' }));
    expect(screen.getByRole('tabpanel').textContent).toBe(MARKDOWN);
    await userEvent.click(screen.getByRole('button', { name: 'Copiar Markdown' }));
    expect(writeText).toHaveBeenCalledWith(MARKDOWN);
    vi.restoreAllMocks();
  });

  it('"Reintentar" vuelve a crear la importación y muestra la vista previa', async () => {
    const real = await import('../components/MarkdownPreview');
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('chunk perdido'))
      .mockResolvedValueOnce(real);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    await renderResult(MARKDOWN, loader);

    await userEvent.click(await screen.findByRole('button', { name: 'Reintentar' }));

    expect(await screen.findByRole('heading', { name: 'Historia de usuario' })).toBeVisible();
    expect(loader).toHaveBeenCalledTimes(2);
    vi.restoreAllMocks();
  });
});
