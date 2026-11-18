export const BUDGET_BYTES: number;
export interface MeasuredFile {
  file: string;
  gzipBytes: number;
  isPreview: boolean;
}
export interface Measured {
  files: MeasuredFile[];
  totalGzipBytes: number;
}
export function initialFileNames(html: string): string[];
export function measureInitialLoad(distDir: string): Measured;
export function evaluateBundle(
  measured: Measured,
  budget?: number,
): { ok: boolean; problems: string[] };
