/** Validación del título (BR5.1) y del contexto (BR5.3), igual que el servicio: recorta y cuenta puntos de código. */

export const TITLE_MAX = 200;
export const CONTEXT_MAX = 500;

export const TITLE_EMPTY_MESSAGE = 'Escribe un titulo para generar la historia.';
export const TITLE_TOO_LONG_MESSAGE = 'El titulo no puede superar 200 caracteres.';
export const CONTEXT_EMPTY_MESSAGE = 'Agrega contexto para generar la historia.';
export const CONTEXT_TOO_LONG_MESSAGE = 'El contexto no puede superar 500 caracteres.';

export type Validation = { ok: true; value: string } | { ok: false; message: string };

/** Longitud en puntos de código Unicode (no en unidades de UTF-16). */
export function codePointLength(text: string): number {
  let count = 0;
  for (const _ of text) {
    void _;
    count += 1;
  }
  return count;
}

/** Longitud que cuenta el servicio y muestra el contador: texto recortado, en puntos de código. */
export function trimmedLength(text: string): number {
  return codePointLength(text.trim());
}

function validate(raw: string, max: number, emptyMessage: string, tooLongMessage: string) {
  const value = raw.trim();
  if (value === '') return { ok: false, message: emptyMessage } as const;
  if (codePointLength(value) > max) return { ok: false, message: tooLongMessage } as const;
  return { ok: true, value } as const;
}

export function validateTitle(raw: string): Validation {
  return validate(raw, TITLE_MAX, TITLE_EMPTY_MESSAGE, TITLE_TOO_LONG_MESSAGE);
}

export function validateContext(raw: string): Validation {
  return validate(raw, CONTEXT_MAX, CONTEXT_EMPTY_MESSAGE, CONTEXT_TOO_LONG_MESSAGE);
}
