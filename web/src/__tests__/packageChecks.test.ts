import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { makeTempDir, randomContent, removeDir, writeFixture } from '../../scripts/fixtures.mjs';
import { BUDGET_BYTES, evaluateBundle, measureInitialLoad } from '../../scripts/check-bundle.mjs';
import { checkIndexHtml, findInlineScripts } from '../../scripts/check-inline.mjs';
import { scanContent, scanDirectory } from '../../scripts/check-secrets.mjs';

let dist: string;

function write(relative: string, content: string | Uint8Array) {
  writeFixture(dist, relative, content);
}

function indexHtml(scripts: string[], preloads: string[] = []) {
  return [
    '<!doctype html><html><head>',
    ...scripts.map((src) => `<script type="module" crossorigin src="${src}"></script>`),
    ...preloads.map((href) => `<link rel="modulepreload" crossorigin href="${href}">`),
    '</head><body><div id="root"></div></body></html>',
  ].join('\n');
}

beforeEach(() => {
  dist = makeTempDir();
});

afterEach(() => {
  removeDir(dist);
});

describe('check:bundle (NFR1.3)', () => {
  it('suma el gzip de los script y modulepreload y deja fuera la carga diferida', () => {
    write('index.html', indexHtml(['/assets/index-a.js'], ['/assets/react-b.js']));
    write('assets/index-a.js', 'export const a = 1;'.repeat(200));
    write('assets/react-b.js', 'export const b = 2;'.repeat(200));
    write('assets/MarkdownPreview-c.js', 'export const c = 3;'.repeat(200));

    const measured = measureInitialLoad(dist);

    expect(measured.files.map((file) => file.file).sort()).toEqual([
      'assets/index-a.js',
      'assets/react-b.js',
    ]);
    expect(measured.totalGzipBytes).toBeGreaterThan(0);
    expect(evaluateBundle(measured)).toEqual({ ok: true, problems: [] });
    expect(BUDGET_BYTES).toBe(400 * 1024);
  });

  it('falla por encima del presupuesto', () => {
    write('index.html', indexHtml(['/assets/index-a.js']));
    write('assets/index-a.js', randomContent(4096));

    const result = evaluateBundle(measureInitialLoad(dist), 1024);

    expect(result.ok).toBe(false);
    expect(result.problems.join(' ')).toMatch(/presupuesto/i);
  });

  it('falla si la vista previa entra en la carga inicial, por nombre o por contenido', () => {
    write('index.html', indexHtml(['/assets/index-a.js'], ['/assets/MarkdownPreview-c.js']));
    write('assets/index-a.js', 'export const a = 1;');
    write('assets/MarkdownPreview-c.js', 'export const c = 3;');
    expect(evaluateBundle(measureInitialLoad(dist)).ok).toBe(false);

    write('index.html', indexHtml(['/assets/index-a.js']));
    write('assets/index-a.js', 'const props = { skipHtml: true, urlTransform: x };');
    const byContent = evaluateBundle(measureInitialLoad(dist));
    expect(byContent.ok).toBe(false);
    expect(byContent.problems.join(' ')).toMatch(/vista previa/i);
  });

  it('falla con un mensaje claro si falta index.html o un archivo referenciado', () => {
    expect(() => measureInitialLoad(dist)).toThrow(/index\.html/);

    write('index.html', indexHtml(['/assets/falta.js']));
    expect(() => measureInitialLoad(dist)).toThrow(/falta\.js/);
  });
});

describe('check:secrets (NFR5.1)', () => {
  it.each([
    ['clave de acceso de AWS', 'const k = "AKIAABCDEFGHIJKLMNOP";'],
    ['clave temporal de AWS', 'const k = "ASIAABCDEFGHIJKLMNOP";'],
    ['aws_secret_access_key', 'aws_secret_access_key=abc'],
    ['client_secret con valor', 'const o = { client_secret: "s3cr3t-value" };'],
    ['clave privada', '-----BEGIN RSA PRIVATE KEY-----'],
  ])('detecta %s', (_name, text) => {
    expect(scanContent('assets/x.js', text)).toHaveLength(1);
  });

  it('no marca el nombre client_secret usado como identificador de la biblioteca', () => {
    const library =
      'exchangeCode({client_secret:s=this._settings.client_secret,scope:i}){a.append("client_secret",s)}';

    expect(scanContent('assets/oidc.js', library)).toEqual([]);
  });

  it('recorre el directorio de forma recursiva e informa el archivo, sin mostrar el valor', () => {
    write('assets/ok.js', 'export const x = 1;');
    write('assets/nested/mal.js', 'const k = "AKIAABCDEFGHIJKLMNOP";');

    const findings = scanDirectory(dist);

    expect(findings).toHaveLength(1);
    expect(findings[0].file).toContain('mal.js');
    expect(JSON.stringify(findings)).not.toContain('AKIAABCDEFGHIJKLMNOP');
  });
});

describe('check:inline (NFR5.4)', () => {
  it('detecta un script sin src y permite los que traen src', () => {
    expect(findInlineScripts('<script type="module" src="/a.js"></script>')).toEqual([]);
    expect(findInlineScripts('<script>alert(1)</script>')).toHaveLength(1);
    expect(findInlineScripts('<script type="module">import("x")</script>')).toHaveLength(1);
  });

  it('revisa dist/index.html y falla ante cualquier script en línea', () => {
    write('index.html', indexHtml(['/assets/index-a.js']));
    expect(checkIndexHtml(dist)).toEqual({ ok: true, problems: [] });

    write('index.html', `${indexHtml(['/assets/index-a.js'])}<script>var x = 1;</script>`);
    const result = checkIndexHtml(dist);
    expect(result.ok).toBe(false);
    expect(result.problems[0]).toMatch(/sin src/i);
  });

  it('falla con un mensaje claro si no existe dist/index.html', () => {
    expect(checkIndexHtml(dist).ok).toBe(false);
  });
});
