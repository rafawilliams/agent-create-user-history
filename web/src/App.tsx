import { Box, Container } from '@mui/material';
import AppHeader from './components/AppHeader';
import LoginButtons from './components/LoginButtons';
import { FailureAlert, LoadingStatus } from './components/StatusMessage';
import StoryForm from './components/StoryForm';
import {
  ACCESS_DENIED_MESSAGE,
  GENERIC_FAILURE_MESSAGE,
  SESSION_EXPIRED_MESSAGE,
} from './api/client';
import type { Services } from './services';
import { useStoryScreen } from './state/useStoryScreen';

/** Elige entre S1 (acceso) y S2 (pantalla principal) según el estado de la pantalla (ENT-002). */
export default function App({ services }: { services: Services }) {
  const screen = useStoryScreen(services);
  const { state } = screen;
  const inSession = ['idle', 'needsContext', 'generating', 'result', 'failed'].includes(state.kind);
  const sessionCheckFailed = state.kind === 'failed' && state.failure?.retry === 'session';

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppHeader showLogout={inSession} onLogout={screen.logout} />
      <Container component="main" maxWidth="md" sx={{ py: 4 }}>
        {state.kind === 'signedOut' && (
          <LoginButtons showError={state.authError} onSignIn={screen.signIn} />
        )}
        {state.kind === 'signingIn' && <LoadingStatus text="Iniciando sesión" />}
        {state.kind === 'sessionExpired' && (
          <FailureAlert
            message={SESSION_EXPIRED_MESSAGE}
            actionLabel="Iniciar sesión de nuevo"
            onAction={screen.restartSignIn}
          />
        )}
        {state.kind === 'accessDenied' && (
          <FailureAlert
            message={ACCESS_DENIED_MESSAGE}
            actionLabel="Cerrar sesión"
            onAction={screen.logout}
          />
        )}
        {sessionCheckFailed && (
          <FailureAlert
            message={state.failure?.message ?? GENERIC_FAILURE_MESSAGE}
            actionLabel="Reintentar"
            onAction={screen.retry}
          />
        )}
        {inSession && !sessionCheckFailed && <StoryForm screen={screen} />}
      </Container>
    </Box>
  );
}
