import { Alert, Box, Button, CircularProgress } from '@mui/material';
import { useEffect, useRef, useState } from 'react';

/** Carga: indicador con texto en una región de estado (AC5.1.1). */
export function LoadingStatus({ text }: { text: string }) {
  return (
    <Box
      role="status"
      aria-live="polite"
      sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 2 }}
    >
      <CircularProgress size={20} aria-hidden="true" />
      <span>{text}</span>
    </Box>
  );
}

/** true mientras `until` (ms) no haya pasado; se actualiza solo con un temporizador. */
function useBlocked(until: number | null): boolean {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (until === null) return;
    const remaining = until - Date.now();
    if (remaining <= 0) {
      setNow(Date.now());
      return;
    }
    const timer = setTimeout(() => setNow(Date.now()), remaining);
    return () => clearTimeout(timer);
  }, [until]);
  return until !== null && now < until;
}

interface FailureAlertProps {
  message: string;
  /** Texto del botón de la acción; null si no se ofrece ninguna. */
  actionLabel: string | null;
  /** Hasta cuándo (ms) la acción queda desactivada. */
  blockedUntil?: number | null;
  onAction?: () => void;
}

/** Fallo con role="alert", icono y texto; el foco pasa a la acción cuando está disponible. */
export function FailureAlert({
  message,
  actionLabel,
  blockedUntil = null,
  onAction,
}: FailureAlertProps) {
  const blocked = useBlocked(blockedUntil);
  const actionRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!blocked) actionRef.current?.focus();
  }, [blocked]);

  return (
    <Alert
      severity="error"
      sx={{ alignItems: 'center' }}
      action={
        actionLabel !== null ? (
          <Button
            ref={actionRef}
            color="inherit"
            variant="outlined"
            size="small"
            disabled={blocked}
            onClick={onAction}
          >
            {actionLabel}
          </Button>
        ) : undefined
      }
    >
      {message}
    </Alert>
  );
}
