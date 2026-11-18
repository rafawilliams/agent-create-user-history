import { Alert, Box, Button } from '@mui/material';
import type { StoryScreen } from '../state/useStoryScreen';
import ContextField from './ContextField';
import ResultView from './ResultView';
import { FailureAlert, LoadingStatus } from './StatusMessage';
import TitleField from './TitleField';

/** S2: título, contexto, generación, fallos y resultado (BR5.1 a BR5.5). */
export default function StoryForm({ screen }: { screen: StoryScreen }) {
  const { state } = screen;
  const generating = state.kind === 'generating';
  const failure = state.failure;

  return (
    <Box
      component="form"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        screen.submit();
      }}
      sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
    >
      {state.notice !== null && (
        <Alert severity="info" role="status">
          {state.notice}
        </Alert>
      )}
      <TitleField
        value={screen.title}
        error={state.titleError}
        disabled={generating}
        focusTick={screen.focus.title}
        onChange={screen.setTitle}
      />
      {screen.showContext && (
        <ContextField
          hint={state.contextMessage}
          value={screen.context}
          error={state.contextError}
          disabled={generating}
          focusTick={screen.focus.context}
          onChange={screen.setContext}
        />
      )}
      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={generating}
        sx={{ width: { xs: '100%', sm: 'auto' }, alignSelf: { sm: 'flex-start' } }}
      >
        Generar historia
      </Button>
      {generating && <LoadingStatus text="Generando la historia" />}
      {state.kind === 'failed' && failure !== null && (
        <FailureAlert
          message={failure.message}
          actionLabel={failure.retryable ? 'Reintentar' : null}
          blockedUntil={failure.blockedUntil}
          onAction={screen.retry}
        />
      )}
      {state.kind === 'result' && state.result !== null && (
        <ResultView markdown={state.result.markdown} />
      )}
    </Box>
  );
}
