/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

/**
 * Agrupa en piezas propias React, MUI y oidc-client-ts (cache del navegador). Todo lo demas,
 * incluido react-markdown y sus dependencias, queda fuera de estos grupos: solo lo importa la
 * vista previa diferida, de modo que nunca entra en la carga inicial (NFR1.3).
 */
export function manualChunk(id: string): string | undefined {
  if (!id.includes('node_modules')) return undefined;
  if (/node_modules\/(react|react-dom|scheduler)\//.test(id)) return 'react';
  if (/node_modules\/(@mui|@emotion)\//.test(id)) return 'mui';
  if (id.includes('node_modules/oidc-client-ts/')) return 'oidc';
  return undefined;
}

export default defineConfig({
  plugins: [react()],
  build: {
    // browserslist (NFR7.2): ultimas versiones de Chrome y Edge; esbuild necesita un destino explicito.
    target: ['chrome120', 'edge120'],
    rollupOptions: { output: { manualChunks: manualChunk } },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.ts'],
    include: ['src/__tests__/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/__tests__/**', 'src/setupTests.ts', 'src/main.tsx', 'src/**/*.d.ts'],
      thresholds: { lines: 80 },
    },
  },
});
