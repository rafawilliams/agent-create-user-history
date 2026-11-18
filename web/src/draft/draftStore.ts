/**
 * Copia temporal de título y contexto (ENT-003, BR5.6, NFR4.4) en sessionStorage de la pestaña.
 * Nunca contiene el token. Un fallo del almacenamiento nunca interrumpe la pantalla.
 */

export const DRAFT_KEY = 'story-web.draft';

export interface Draft {
  title: string;
  context: string;
  accountId: string;
}

export type RestoreResult =
  { status: 'none' } | { status: 'restored'; draft: Draft } | { status: 'discarded' };

function isDraft(value: unknown): value is Draft {
  if (typeof value !== 'object' || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.title === 'string' &&
    typeof candidate.context === 'string' &&
    typeof candidate.accountId === 'string'
  );
}

export function saveDraft(draft: Draft): void {
  try {
    sessionStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({ title: draft.title, context: draft.context, accountId: draft.accountId }),
    );
  } catch {
    // sin almacenamiento disponible: se pierde la copia, la pantalla sigue funcionando
  }
}

export function clearDraft(): void {
  try {
    sessionStorage.removeItem(DRAFT_KEY);
  } catch {
    // nada que borrar si el almacenamiento no está disponible
  }
}

/** Lee la copia y la borra siempre; solo se restaura con la misma cuenta. */
export function restoreDraft(accountId: string): RestoreResult {
  let parsed: unknown = null;
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (raw === null) return { status: 'none' };
    parsed = JSON.parse(raw);
  } catch {
    parsed = null;
  }
  clearDraft();
  if (!isDraft(parsed)) return { status: 'none' };
  return parsed.accountId === accountId
    ? { status: 'restored', draft: parsed }
    : { status: 'discarded' };
}
