// Falla ante cualquier <script> sin src en dist/index.html (NFR5.4: la política de contenido no
// permite scripts en línea). Uso: node scripts/check-inline.mjs [dist]
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

/** Etiquetas <script> que no traen src. */
export function findInlineScripts(html) {
  return [...html.matchAll(/<script\b([^>]*)>/gi)]
    .map((match) => match[0])
    .filter((tag) => !/\bsrc\s*=/i.test(tag));
}

export function checkIndexHtml(distDir) {
  const indexPath = join(distDir, 'index.html');
  if (!existsSync(indexPath)) {
    return { ok: false, problems: [`No existe ${indexPath}: ejecuta primero "npm run build".`] };
  }
  const inline = findInlineScripts(readFileSync(indexPath, 'utf8'));
  return {
    ok: inline.length === 0,
    problems: inline.map((tag) => `Hay un <script> sin src en index.html: ${tag}`),
  };
}

function main() {
  const result = checkIndexHtml(resolve(process.argv[2] ?? 'dist'));
  for (const problem of result.problems) console.error(problem);
  if (result.ok) console.log('index.html no tiene scripts en línea.');
  process.exit(result.ok ? 0 : 1);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
