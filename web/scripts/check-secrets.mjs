// Busca claves y secretos en dist/ (NFR5.1). Uso: node scripts/check-secrets.mjs [dist]
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Patrones de cicd-pipeline.md. `client_secret` solo se marca cuando se le asigna un valor
// literal: oidc-client-ts contiene ese nombre como identificador de sus ajustes opcionales y
// el cliente de Cognito es público (sin secreto).
export const SECRET_PATTERNS = [
  { name: 'clave de acceso de AWS (AKIA)', regex: /AKIA[0-9A-Z]{16}/ },
  { name: 'clave temporal de AWS (ASIA)', regex: /ASIA[0-9A-Z]{16}/ },
  { name: 'aws_secret_access_key', regex: /aws_secret_access_key/i },
  { name: 'client_secret con valor', regex: /client_secret["']?\s*[:=]\s*["'][^"']+["']/i },
  { name: 'clave privada', regex: /-----BEGIN/ },
];

const TEXT_EXTENSIONS = new Set(['.js', '.mjs', '.css', '.html', '.json', '.map', '.txt', '.svg']);

/** Hallazgos de un texto; nunca incluyen el valor encontrado. */
export function scanContent(file, text) {
  return SECRET_PATTERNS.filter(({ regex }) => regex.test(text)).map(({ name }) => ({
    file,
    pattern: name,
  }));
}

export function scanDirectory(dir) {
  const findings = [];
  const walk = (current) => {
    for (const entry of readdirSync(current)) {
      const path = join(current, entry);
      if (statSync(path).isDirectory()) walk(path);
      else if (TEXT_EXTENSIONS.has(extname(path))) {
        findings.push(...scanContent(path, readFileSync(path, 'utf8')));
      }
    }
  };
  walk(dir);
  return findings;
}

function main() {
  const dist = resolve(process.argv[2] ?? 'dist');
  try {
    const findings = scanDirectory(dist);
    for (const finding of findings) console.error(`${finding.file}: ${finding.pattern}`);
    if (findings.length === 0) console.log('Sin secretos ni claves en dist.');
    process.exit(findings.length === 0 ? 0 : 1);
  } catch (error) {
    console.error(`No se pudo revisar ${dist}: ${error.message}`);
    process.exit(1);
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
