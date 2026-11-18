import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { resetCallbackForTests } from '../auth/authClient';
import { Root } from '../bootstrap';
import { resetStartupForTests } from '../state/useStoryScreen';

const VALID_ENV = {
  VITE_API_URL: 'https://api.example.invalid',
  VITE_COGNITO_REGION: 'us-east-1',
  VITE_COGNITO_USER_POOL_ID: 'us-east-1_AbCdEf123',
  VITE_COGNITO_DOMAIN: 'agente.auth.us-east-1.amazoncognito.com',
  VITE_COGNITO_CLIENT_ID: 'client123',
};

beforeEach(() => {
  resetCallbackForTests();
  resetStartupForTests();
  window.history.replaceState({}, '', '/');
});

describe('Root (NFR5.1: configuración al arrancar)', () => {
  it('sin variables muestra un error de configuración y no ofrece iniciar sesión', () => {
    render(<Root env={{}} />);

    expect(screen.getByRole('alert')).toHaveTextContent('La pantalla no está configurada');
    expect(screen.queryByRole('button', { name: 'Continuar con Gmail' })).toBeNull();
  });

  it('el error de configuración no muestra los valores recibidos', () => {
    render(
      <Root env={{ ...VALID_ENV, VITE_API_URL: 'https://u:CLAVE-SECRETA@api.example.invalid' }} />,
    );

    expect(screen.getByRole('alert').textContent).not.toContain('CLAVE-SECRETA');
  });

  it('con la configuración completa muestra S1 con los dos proveedores', async () => {
    render(<Root env={VALID_ENV} />);

    expect(await screen.findByRole('button', { name: 'Continuar con Gmail' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Continuar con Outlook' })).toBeVisible();
  });
});
