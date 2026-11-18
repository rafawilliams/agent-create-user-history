// Ayudas de las pruebas de las comprobaciones del paquete: crean y borran directorios temporales
// dentro del proyecto (node_modules/.cache), nunca fuera de él.
import { randomBytes } from 'node:crypto';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

export function makeTempDir() {
  const cache = join(process.cwd(), 'node_modules', '.cache');
  mkdirSync(cache, { recursive: true });
  return mkdtempSync(join(cache, 'u5-checks-'));
}

export function writeFixture(root, relative, content) {
  const target = join(root, relative);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

export function removeDir(dir) {
  rmSync(dir, { recursive: true, force: true });
}

export function randomContent(bytes) {
  return randomBytes(bytes);
}
