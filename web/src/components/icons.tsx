import { SvgIcon, type SvgIconProps } from '@mui/material';

/** Iconos decorativos (el texto siempre acompaña, por eso van ocultos a los lectores de pantalla). */

export function ErrorIcon(props: SvgIconProps) {
  return (
    <SvgIcon fontSize="small" aria-hidden="true" {...props}>
      <path d="M11 15h2v2h-2zm0-8h2v6h-2zm.99-5C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z" />
    </SvgIcon>
  );
}

export function CheckIcon(props: SvgIconProps) {
  return (
    <SvgIcon fontSize="small" aria-hidden="true" {...props}>
      <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </SvgIcon>
  );
}

export function MenuIcon(props: SvgIconProps) {
  return (
    <SvgIcon aria-hidden="true" {...props}>
      <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
    </SvgIcon>
  );
}
