import { describe, expect, it } from 'vitest';
import { ConfigError, loadConfig } from '../config';

const VALID_ENV = {
  VITE_API_URL: 'https://api.example.invalid/',
  VITE_COGNITO_REGION: 'us-east-1',
  VITE_COGNITO_USER_POOL_ID: 'us-east-1_AbCdEf123',
  VITE_COGNITO_DOMAIN: 'agente.auth.us-east-1.amazoncognito.com',
  VITE_COGNITO_CLIENT_ID: 'client123',
};

const ORIGIN = 'https://sitio.example.invalid';

describe('loadConfig', () => {
  it('devuelve la configuración pública con la dirección de retorno en la raíz del sitio', () => {
    const config = loadConfig(VALID_ENV, ORIGIN);

    expect(config).toEqual({
      apiUrl: 'https://api.example.invalid',
      region: 'us-east-1',
      userPoolId: 'us-east-1_AbCdEf123',
      cognitoDomain: 'agente.auth.us-east-1.amazoncognito.com',
      clientId: 'client123',
      redirectUri: 'https://sitio.example.invalid/',
    });
  });

  it('acepta el dominio de Cognito con esquema y lo normaliza a solo el host', () => {
    const config = loadConfig(
      { ...VALID_ENV, VITE_COGNITO_DOMAIN: 'https://agente.auth.us-east-1.amazoncognito.com/' },
      ORIGIN,
    );

    expect(config.cognitoDomain).toBe('agente.auth.us-east-1.amazoncognito.com');
  });

  it.each(Object.keys(VALID_ENV))('falla con %s ausente y nombra la variable', (name) => {
    const env: Record<string, string | undefined> = { ...VALID_ENV };
    delete env[name];

    expect(() => loadConfig(env, ORIGIN)).toThrow(ConfigError);
    try {
      loadConfig(env, ORIGIN);
    } catch (error) {
      expect((error as ConfigError).missing).toEqual([name]);
    }
  });

  it('falla con una variable vacía o solo de espacios', () => {
    expect(() => loadConfig({ ...VALID_ENV, VITE_API_URL: '' }, ORIGIN)).toThrow(ConfigError);
    expect(() => loadConfig({ ...VALID_ENV, VITE_COGNITO_CLIENT_ID: '   ' }, ORIGIN)).toThrow(
      ConfigError,
    );
  });

  it('no acepta una dirección con usuario y contraseña incrustados', () => {
    expect(() =>
      loadConfig(
        { ...VALID_ENV, VITE_API_URL: 'https://usuario:clave@api.example.invalid' },
        ORIGIN,
      ),
    ).toThrow(ConfigError);
  });

  it('no acepta valores con forma de clave de AWS ni una variable de secreto', () => {
    expect(() =>
      loadConfig({ ...VALID_ENV, VITE_COGNITO_CLIENT_ID: 'AKIAABCDEFGHIJKLMNOP' }, ORIGIN),
    ).toThrow(ConfigError);
    expect(() => loadConfig({ ...VALID_ENV, VITE_COGNITO_CLIENT_SECRET: 'x' }, ORIGIN)).toThrow(
      ConfigError,
    );
  });

  it('exige https para el servicio, salvo localhost para el desarrollo', () => {
    expect(() =>
      loadConfig({ ...VALID_ENV, VITE_API_URL: 'http://api.example.invalid' }, ORIGIN),
    ).toThrow(ConfigError);
    expect(loadConfig({ ...VALID_ENV, VITE_API_URL: 'http://localhost:3000' }, ORIGIN).apiUrl).toBe(
      'http://localhost:3000',
    );
  });

  it('el mensaje de error no contiene los valores recibidos', () => {
    try {
      loadConfig({ ...VALID_ENV, VITE_API_URL: 'https://u:SECRETO@api.example.invalid' }, ORIGIN);
      expect.unreachable();
    } catch (error) {
      expect((error as Error).message).not.toContain('SECRETO');
    }
  });
});
