import { Alert, Box, Button, CircularProgress, Paper, Tab, Tabs } from '@mui/material';
import {
  Component,
  Suspense,
  lazy,
  useMemo,
  useState,
  type ComponentType,
  type ReactNode,
} from 'react';
import { CheckIcon } from './icons';

export type PreviewLoader = () => Promise<{ default: ComponentType<{ markdown: string }> }>;

// Solo la vista previa es diferida: las pestañas, el texto Markdown y el copiado no dependen de ella.
const defaultLoader: PreviewLoader = () => import('./MarkdownPreview');

export const COPIED_MESSAGE = 'Markdown copiado';
export const COPY_FAILED_MESSAGE = 'No se pudo copiar. Selecciona el texto y cópialo a mano.';
export const PREVIEW_FAILED_MESSAGE = 'No se pudo cargar la vista previa. Usa la pestaña Markdown.';

interface BoundaryProps {
  onRetry: () => void;
  children: ReactNode;
}

/** Barrera de errores de la vista previa: si la importación falla, avisa y permite reintentar. */
class PreviewBoundary extends Component<BoundaryProps, { failed: boolean }> {
  state = { failed: false };

  // El error se contiene aquí y no se registra: el contenido de la persona no va a la consola.
  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <Alert
        severity="warning"
        action={
          <Button color="inherit" size="small" onClick={this.props.onRetry}>
            Reintentar
          </Button>
        }
      >
        {PREVIEW_FAILED_MESSAGE}
      </Alert>
    );
  }
}

function PreviewPane({ markdown, loader }: { markdown: string; loader: PreviewLoader }) {
  const [attempt, setAttempt] = useState(0);
  // La promesa rechazada queda en caché: cada reintento recrea la importación diferida.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const Preview = useMemo(() => lazy(loader), [loader, attempt]);

  return (
    <PreviewBoundary key={attempt} onRetry={() => setAttempt((value) => value + 1)}>
      <Suspense
        fallback={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 2 }}>
            <CircularProgress size={20} aria-hidden="true" />
            <span>Cargando vista previa</span>
          </Box>
        }
      >
        <Preview markdown={markdown} />
      </Suspense>
    </PreviewBoundary>
  );
}

interface ResultViewProps {
  markdown: string;
  /** Solo para pruebas: permite simular la carga diferida. */
  previewLoader?: PreviewLoader;
}

/** Resultado en dos pestañas con el mismo contenido y el botón de copiado exacto (BR5.5). */
export default function ResultView({ markdown, previewLoader = defaultLoader }: ResultViewProps) {
  const [tab, setTab] = useState<'preview' | 'markdown'>('preview');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');

  async function copy() {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopyState('copied');
    } catch {
      setCopyState('failed');
    }
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Tabs
        value={tab}
        onChange={(_event, value: 'preview' | 'markdown') => setTab(value)}
        aria-label="Resultado"
        selectionFollowsFocus
        variant="scrollable"
      >
        <Tab label="Vista previa" value="preview" id="tab-preview" aria-controls="panel-result" />
        <Tab label="Markdown" value="markdown" id="tab-markdown" aria-controls="panel-result" />
      </Tabs>
      <Box role="tabpanel" id="panel-result" aria-labelledby={`tab-${tab}`} sx={{ py: 2 }}>
        {tab === 'preview' ? (
          <PreviewPane markdown={markdown} loader={previewLoader} />
        ) : (
          <Box
            component="pre"
            tabIndex={0}
            sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontFamily: 'monospace', m: 0 }}
          >
            {markdown}
          </Box>
        )}
      </Box>
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
        <Button
          variant="outlined"
          onClick={() => void copy()}
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          Copiar Markdown
        </Button>
        <Box
          role="status"
          aria-live="polite"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          {copyState === 'copied' && (
            <>
              <CheckIcon color="success" />
              <span>{COPIED_MESSAGE}</span>
            </>
          )}
          {copyState === 'failed' && <span>{COPY_FAILED_MESSAGE}</span>}
        </Box>
      </Box>
    </Paper>
  );
}
