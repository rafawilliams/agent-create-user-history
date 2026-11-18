/** Configuración pública de la pantalla: solo variables VITE_ sin secretos (NFR5.1). */

export interface AppConfig {
  /** Dirección base del servicio, sin barra final. */
  apiUrl: string;
  region: string;
  userPoolId: string;
  /** Host del dominio alojado del grupo de usuarios, sin esquema. */
  cognitoDomain: string;
  clientId: string;
  /** Raíz del sitio: dirección de retorno y de cierre de sesión (valor exacto). */
  redirectUri: string;
}

export class ConfigError extends Error {
  readonly missing: string[];

  constructor(message: string, missing: string[] = []) {
    super(message);
    this.name = 'ConfigError';
    this.missing = missing;
  }
}

const REQUIRED = [
  'VITE_API_URL',
  'VITE_COGNITO_REGION',
  'VITE_COGNITO_USER_POOL_ID',
  'VITE_COGNITO_DOMAIN',
  'VITE_COGNITO_CLIENT_ID',
] as const;

const AWS_KEY_PATTERN = /\b(AKIA|ASIA)[0-9A-Z]{16}\b/;
const SECRET_NAME_PATTERN = /secret|private[_-]?key|password/i;

function readValue(env: Record<string, unknown>, name: string): string {
  const value = env[name];
  return typeof value === 'string' ? value.trim() : '';
}

function parseUrl(value: string): URL | null {
  try {
    return new URL(value);
  } catch {
    return null;
  }
}

/** Lee y valida la configuración. Los mensajes de error nunca incluyen los valores recibidos. */
export function loadConfig(
  env: Record<string, unknown> = import.meta.env,
  origin: string = window.location.origin,
): AppConfig {
  const secretVariable = Object.keys(env).find(
    (name) => name.startsWith('VITE_') && SECRET_NAME_PATTERN.test(name),
  );
  if (secretVariable !== undefined) {
    throw new ConfigError('La configuración pública no puede incluir secretos.');
  }

  const missing = REQUIRED.filter((name) => readValue(env, name) === '');
  if (missing.length > 0) {
    throw new ConfigError(`Faltan variables de configuración: ${missing.join(', ')}.`, [
      ...missing,
    ]);
  }

  const values = Object.fromEntries(REQUIRED.map((name) => [name, readValue(env, name)]));
  if (Object.values(values).some((value) => AWS_KEY_PATTERN.test(value))) {
    throw new ConfigError('La configuración pública no puede incluir claves de AWS.');
  }

  const api = parseUrl(values.VITE_API_URL);
  const isLocalhost = api?.hostname === 'localhost' || api?.hostname === '127.0.0.1';
  if (
    api === null ||
    api.username !== '' ||
    api.password !== '' ||
    (api.protocol !== 'https:' && !(api.protocol === 'http:' && isLocalhost))
  ) {
    throw new ConfigError('VITE_API_URL debe ser una dirección https sin credenciales.', [
      'VITE_API_URL',
    ]);
  }

  const domainUrl = parseUrl(
    values.VITE_COGNITO_DOMAIN.includes('://')
      ? values.VITE_COGNITO_DOMAIN
      : `https://${values.VITE_COGNITO_DOMAIN}`,
  );
  if (domainUrl === null || domainUrl.protocol !== 'https:' || domainUrl.username !== '') {
    throw new ConfigError('VITE_COGNITO_DOMAIN debe ser un dominio https.', [
      'VITE_COGNITO_DOMAIN',
    ]);
  }

  return {
    apiUrl: `${api.origin}${api.pathname.replace(/\/+$/, '')}`,
    region: values.VITE_COGNITO_REGION,
    userPoolId: values.VITE_COGNITO_USER_POOL_ID,
    cognitoDomain: domainUrl.host,
    clientId: values.VITE_COGNITO_CLIENT_ID,
    redirectUri: `${origin.replace(/\/+$/, '')}/`,
  };
}
