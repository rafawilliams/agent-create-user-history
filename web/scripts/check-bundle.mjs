// Presupuesto de la carga inicial (NFR1.3): 400 KB de JavaScript comprimido (gzip) y la vista
// previa de Markdown fuera de la carga inicial. Uso: node scripts/check-bundle.mjs [dist]
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

export const BUDGET_BYTES = 400 * 1024;

// Señales de que un archivo es la vista previa diferida: su nombre o propiedades de react-markdown
// (los nombres de propiedades sobreviven a la minificación).
const PREVIEW_NAME = /MarkdownPreview/i;
const PREVIEW_MARKERS = ['skipHtml', 'urlTransform'];

/** Archivos que index.html carga al arrancar: script y modulepreload (no las importaciones diferidas). */
export function initialFileNames(html) {
  const names = [];
  for (const match of html.matchAll(/<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/gi)) {
    names.push(match[1]);
  }
  for (const match of html.matchAll(/<link\b[^>]*>/gi)) {
    const tag = match[0];
    if (!/rel\s*=\s*["']modulepreload["']/i.test(tag)) continue;
    const href = /href\s*=\s*["']([^"']+)["']/i.exec(tag);
    if (href) names.push(href[1]);
  }
  return [...new Set(names)].map((name) => name.replace(/^\/+/, ''));
}

export function measureInitialLoad(distDir) {
  const indexPath = join(distDir, 'index.html');
  if (!existsSync(indexPath)) {
    throw new Error(`No existe ${indexPath}: ejecuta primero "npm run build".`);
  }
  const files = initialFileNames(readFileSync(indexPath, 'utf8')).map((file) => {
    const path = join(distDir, file);
    if (!existsSync(path)) throw new Error(`index.html referencia ${file}, que no existe en dist.`);
    const content = readFileSync(path);
    return {
      file,
      gzipBytes: gzipSync(content).length,
      isPreview:
        PREVIEW_NAME.test(file) || PREVIEW_MARKERS.every((marker) => content.includes(marker)),
    };
  });
  return { files, totalGzipBytes: files.reduce((sum, file) => sum + file.gzipBytes, 0) };
}

export function evaluateBundle(measured, budget = BUDGET_BYTES) {
  const problems = [];
  if (measured.totalGzipBytes > budget) {
    problems.push(
      `La carga inicial pesa ${measured.totalGzipBytes} bytes gzip y supera el presupuesto de ${budget}.`,
    );
  }
  for (const file of measured.files.filter((entry) => entry.isPreview)) {
    problems.push(`La vista previa (${file.file}) está en la carga inicial; debe ser diferida.`);
  }
  return { ok: problems.length === 0, problems };
}

function main() {
  const distDir = resolve(process.argv[2] ?? 'dist');
  try {
    const measured = measureInitialLoad(distDir);
    for (const file of measured.files) console.log(`${file.file}: ${file.gzipBytes} bytes gzip`);
    console.log(
      `Total inicial: ${measured.totalGzipBytes} bytes gzip (presupuesto ${BUDGET_BYTES}).`,
    );
    const result = evaluateBundle(measured);
    for (const problem of result.problems) console.error(problem);
    process.exit(result.ok ? 0 : 1);
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
