import { createTheme, type Theme } from '@mui/material';

/** Tamaño táctil mínimo (NFR7.1, BR5.9). */
const TOUCH_TARGET = 44;

/** Tema de MUI claro u oscuro con la paleta por defecto de Material Design. */
export function createAppTheme(mode: 'light' | 'dark'): Theme {
  const touchTarget = { minHeight: TOUCH_TARGET, minWidth: TOUCH_TARGET };
  return createTheme({
    palette: { mode },
    components: {
      MuiButton: { styleOverrides: { root: touchTarget } },
      MuiIconButton: { styleOverrides: { root: touchTarget } },
      MuiTab: { styleOverrides: { root: touchTarget } },
      MuiOutlinedInput: { styleOverrides: { root: { minHeight: TOUCH_TARGET } } },
    },
  });
}
