/**
 * Vista previa segura del Markdown (BR5.5, NFR4.3). Se carga de forma diferida: es lo único
 * que importa react-markdown. Nunca ejecuta HTML: `skipHtml`, sin plugin de HTML en bruto,
 * solo enlaces http, https y mailto, e imágenes sustituidas por su texto.
 */
import { Box } from '@mui/material';
import Markdown, { type Components } from 'react-markdown';

const ALLOWED_URL = /^(https?:|mailto:)/i;

/** Devuelve una cadena vacía para todo esquema que no sea http, https o mailto. */
export function safeUrl(url: string): string {
  return ALLOWED_URL.test(url.trim()) ? url : '';
}

const components: Components = {
  a({ href, children }) {
    const safe = typeof href === 'string' && href !== '' ? href : undefined;
    return (
      <a href={safe} target={safe ? '_blank' : undefined} rel="noopener noreferrer">
        {children}
      </a>
    );
  },
  // Las imágenes no se cargan: se muestran como texto con su texto alternativo.
  img({ alt }) {
    return <span>{alt ? `[Imagen: ${alt}]` : '[Imagen]'}</span>;
  },
};

export default function MarkdownPreview({ markdown }: { markdown: string }) {
  return (
    <Box
      sx={{
        overflowWrap: 'anywhere',
        '& pre': { overflowX: 'auto', p: 1.5, borderRadius: 1, bgcolor: 'action.hover' },
        '& h1, & h2, & h3': { mt: 2, mb: 1 },
      }}
    >
      <Markdown skipHtml urlTransform={safeUrl} components={components}>
        {markdown}
      </Markdown>
    </Box>
  );
}
