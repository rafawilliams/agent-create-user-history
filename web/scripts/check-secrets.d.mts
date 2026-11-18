export const SECRET_PATTERNS: Array<{ name: string; regex: RegExp }>;
export interface SecretFinding {
  file: string;
  pattern: string;
}
export function scanContent(file: string, text: string): SecretFinding[];
export function scanDirectory(dir: string): SecretFinding[];
