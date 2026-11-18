/**
 * Dueño del token de identidad y de su `exp`, solo en memoria (BR5.6, NFR4.1).
 * Nada de esto se escribe en localStorage, sessionStorage, cookies, la dirección ni la consola.
 */

/** Lo único que se toma del usuario de la biblioteca de inicio de sesión. */
export interface UserLike {
  id_token?: string;
  profile?: { exp?: number };
}

export interface SessionHolder {
  /** Toma el token de identidad y su `exp`; false si el usuario no los trae. */
  setFromUser(user: UserLike): boolean;
  /** Entrega el token solo si no ha vencido. */
  getToken(): string | null;
  /** `exp` del token en segundos desde la época, o null. */
  getExpiresAt(): number | null;
  clear(): void;
}

export function createSessionHolder(now: () => number = Date.now): SessionHolder {
  let token: string | null = null;
  let exp: number | null = null;

  return {
    setFromUser(user) {
      const candidateExp = user.profile?.exp;
      if (typeof user.id_token !== 'string' || user.id_token === '') return false;
      if (typeof candidateExp !== 'number') return false;
      token = user.id_token;
      exp = candidateExp;
      return true;
    },
    getToken() {
      if (token === null || exp === null) return null;
      return now() >= exp * 1000 ? null : token;
    },
    getExpiresAt() {
      return exp;
    },
    clear() {
      token = null;
      exp = null;
    },
  };
}
