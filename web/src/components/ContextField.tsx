import { Box, TextField } from '@mui/material';
import { useEffect, useRef } from 'react';
import { CONTEXT_MAX, trimmedLength } from '../validation';
import { ErrorIcon } from './icons';

interface ContextFieldProps {
  /** Mensaje del servicio bajo el título (NEEDS_CONTEXT); se asocia al campo como descripción. */
  hint: string | null;
  value: string;
  error: string | null;
  disabled: boolean;
  focusTick: number;
  onChange: (value: string) => void;
}

function Message({ text }: { text: string }) {
  return (
    <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <ErrorIcon />
      {text}
    </Box>
  );
}

/** Contexto de hasta 500 caracteres; recibe el foco al aparecer (BR5.3). */
export default function ContextField({
  hint,
  value,
  error,
  disabled,
  focusTick,
  onChange,
}: ContextFieldProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [focusTick]);

  return (
    <TextField
      label="Contexto"
      fullWidth
      multiline
      minRows={3}
      value={value}
      disabled={disabled}
      error={error !== null}
      inputRef={inputRef}
      onChange={(event) => onChange(event.target.value)}
      helperText={
        <>
          {hint !== null && <Message text={hint} />}
          {error !== null && <Message text={error} />}
          <Box component="span" sx={{ display: 'block', textAlign: 'right' }}>
            {trimmedLength(value)} / {CONTEXT_MAX}
          </Box>
        </>
      }
    />
  );
}
