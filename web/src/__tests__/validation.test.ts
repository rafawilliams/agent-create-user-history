import { describe, expect, it } from 'vitest';
import {
  CONTEXT_EMPTY_MESSAGE,
  CONTEXT_MAX,
  CONTEXT_TOO_LONG_MESSAGE,
  TITLE_EMPTY_MESSAGE,
  TITLE_MAX,
  TITLE_TOO_LONG_MESSAGE,
  codePointLength,
  validateContext,
  validateTitle,
} from '../validation';

describe('codePointLength', () => {
  it('cuenta puntos de código Unicode y no unidades de UTF-16', () => {
    expect(codePointLength('abc')).toBe(3);
    expect(codePointLength('a😀b')).toBe(3);
    expect('a😀b'.length).toBe(4);
  });
});

describe('validateTitle (BR5.1)', () => {
  it('usa los mensajes literales de la regla', () => {
    expect(TITLE_EMPTY_MESSAGE).toBe('Escribe un titulo para generar la historia.');
    expect(TITLE_TOO_LONG_MESSAGE).toBe('El titulo no puede superar 200 caracteres.');
  });

  it('recorta los espacios de los bordes y devuelve el valor recortado', () => {
    expect(validateTitle('  Recuperar contraseña  ')).toEqual({
      ok: true,
      value: 'Recuperar contraseña',
    });
  });

  it.each(['', '   ', '\n\t '])('rechaza vacío o solo espacios (%j)', (raw) => {
    expect(validateTitle(raw)).toEqual({ ok: false, message: TITLE_EMPTY_MESSAGE });
  });

  it('acepta exactamente 200 caracteres y rechaza 201', () => {
    expect(validateTitle('a'.repeat(TITLE_MAX)).ok).toBe(true);
    expect(validateTitle('a'.repeat(TITLE_MAX + 1))).toEqual({
      ok: false,
      message: TITLE_TOO_LONG_MESSAGE,
    });
  });

  it('cuenta en puntos de código: 200 emojis valen y 201 no', () => {
    expect(validateTitle('😀'.repeat(200)).ok).toBe(true);
    expect(validateTitle('😀'.repeat(201)).ok).toBe(false);
  });

  it('los espacios de los bordes no cuentan para el límite', () => {
    expect(validateTitle(`  ${'a'.repeat(200)}  `).ok).toBe(true);
  });
});

describe('validateContext (BR5.3)', () => {
  it('usa los mensajes literales de la regla', () => {
    expect(CONTEXT_EMPTY_MESSAGE).toBe('Agrega contexto para generar la historia.');
    expect(CONTEXT_TOO_LONG_MESSAGE).toBe('El contexto no puede superar 500 caracteres.');
  });

  it('rechaza vacío o solo espacios', () => {
    expect(validateContext('   ')).toEqual({ ok: false, message: CONTEXT_EMPTY_MESSAGE });
  });

  it('acepta exactamente 500 y rechaza 501, recortando y contando puntos de código', () => {
    expect(validateContext(` ${'😀'.repeat(CONTEXT_MAX)} `)).toEqual({
      ok: true,
      value: '😀'.repeat(CONTEXT_MAX),
    });
    expect(validateContext('😀'.repeat(CONTEXT_MAX + 1))).toEqual({
      ok: false,
      message: CONTEXT_TOO_LONG_MESSAGE,
    });
  });
});
