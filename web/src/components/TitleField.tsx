import { Box, TextField } from '@mui/material';
import { useEffect, useRef } from 'react';
import { TITLE_MAX, trimmedLength } from '../validation';
import { ErrorIcon } from './icons';

interface TitleFieldProps {
  value: string;
  error: string | null;
  disabled: boolean;
  /** Sube cada vez que el campo debe recibir el foco (validación fallida). */
  focusTick: number;
  onChange: (value: string) => void;
}

/** Título con contador "N / 200" y el error bajo el campo, con icono y texto (BR5.1). */
export default function TitleField({
  value,
  error,
  disabled,
  focusTick,
  onChange,
}: TitleFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (focusTick > 0) inputRef.current?.focus();
  }, [focusTick]);

  return (
    <TextField
      label="Titulo de la funcionalidad"
      placeholder="Por ejemplo: Recuperar contraseña"
      fullWidth
      value={value}
      disabled={disabled}
      error={error !== null}
      inputRef={inputRef}
      onChange={(event) => onChange(event.target.value)}
      helperText={
        <>
          {error !== null && (
            <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <ErrorIcon />
              {error}
            </Box>
          )}
          <Box component="span" sx={{ display: 'block', textAlign: 'right' }}>
            {trimmedLength(value)} / {TITLE_MAX}
          </Box>
        </>
      }
    />
  );
}
