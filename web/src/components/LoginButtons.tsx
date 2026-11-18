import { Alert, Box, Button, Typography } from '@mui/material';
import type { Provider } from '../auth/authClient';

export const AUTH_ERROR_MESSAGE = 'No se pudo iniciar sesión. Inténtalo de nuevo.';

interface LoginButtonsProps {
  /** Muestra el aviso de acceso fallido (BR5.7); los botones siguen disponibles. */
  showError: boolean;
  onSignIn: (provider: Provider) => void;
}

/** S1: "Continuar con Gmail" y "Continuar con Outlook" (BR5.7). No redirige por sí sola. */
export default function LoginButtons({ showError, onSignIn }: LoginButtonsProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 420, mx: 'auto' }}>
      <Typography variant="body1">Inicia sesión para generar tus historias de usuario.</Typography>
      {showError && <Alert severity="error">{AUTH_ERROR_MESSAGE}</Alert>}
      <Button variant="outlined" size="large" fullWidth onClick={() => onSignIn('Google')}>
        Continuar con Gmail
      </Button>
      <Button variant="outlined" size="large" fullWidth onClick={() => onSignIn('Microsoft')}>
        Continuar con Outlook
      </Button>
    </Box>
  );
}
