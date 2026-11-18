## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-18T07:00:00Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Minor | web/src/state/useStoryScreen.ts > logout(); web/src/auth/authClient.ts > signOut | Al pulsar "Cerrar sesion" el estado pasa de inmediato a signedOut (se ven los botones de acceso) pero la navegación a /logout de Cognito espera a que termine DELETE /v1/session, que puede tardar hasta 60 s con la red colgada. Si en ese lapso la persona pulsa "Continuar con Gmail", signinRedirect navega antes y el cierre de Cognito nunca ocurre; el siguiente acceso entraría solo, que es justo lo que BR5.8 quiere evitar. | Mostrar un estado "Cerrando sesión" sin botones de acceso mientras dura el cierre, o acotar DELETE a pocos segundos antes de navegar a Cognito; añadir una prueba de ese caso. | New |
| R-02 | Minor | .github/workflows/ci.yml > comentario de cabecera | El comentario dice que el archivo cubre "Etapas 1 a 4 (u1-walking-skeleton)", pero el trabajo `web` ahora incluye cobertura, presupuesto, auditoría, secretos y scripts en línea de u5. | Actualizar el comentario para que describa lo que ejecuta hoy. | New |
| R-03 | Minor | web/src/__tests__/authClient.test.ts (simulación de oidc-client-ts) | PKCE, validación de state y nonce, intercambio de código y cierre de Cognito se prueban solo contra una biblioteca simulada; ninguna prueba ejerce el comportamiento real de `UserManager` con los metadatos explícitos. code-summary.md y unit-test-instructions.md lo declaran, así que no es un hallazgo de honestidad, pero queda sin cobertura automática. | Conservar en Build and Test una verificación manual explícita (login con Google y Microsoft, state alterado, cancelación, cierre) con responsable, y no darla por cubierta por las 186 pruebas. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `npx vitest run` (web) | PASS: 12 archivos, 186 pruebas en verde | Coincide con code-summary.md; no se vieron `expect(true)`, `.skip` ni `.only`. |
| `npm run lint` | PASS, sin salida | Limpio. |
| `npm run build` (valores VITE_ ficticios) | PASS: `tsc --noEmit` y `vite build` | Coincide con el resumen. |
| `npm run check:bundle` | PASS: 142 958 bytes gzip de 409 600; MarkdownPreview fuera de la carga inicial | La vista previa sí es diferida. |
| `npm run check:secrets` | PASS | En el paquete, `client_secret` aparece solo como identificador de ajustes de oidc-client-ts (`client_secret_post`, `this._settings.client_secret`), sin literal asignado. La relajación del patrón es inocua; los demás patrones siguen intactos. |
| Búsqueda de `localStorage`, `console.` y cookies en `web/src` (sin pruebas) | Sin usos de localStorage, console ni cookies | sessionStorage solo guarda el estado de PKCE (stateStore) y la copia temporal (DRAFT_KEY); el token vive en memoria (`InMemoryWebStorage` y `sessionHolder`). |

### Summary

No hay Critical ni Major abiertos. Revisé el código contra BR5.1 a BR5.10: el token solo está en memoria; el retorno de Cognito se procesa una vez con una promesa de módulo y la dirección se limpia antes de procesarlo; el orden de cierre es DELETE, removeUser, borrado de la copia y navegación con `logout_uri` exacto; la tabla de errores de BR5.4 no muestra texto del servidor; hay bloqueo de 30 s para el 429, corte de 60 s con descarte de respuesta tardía y restauración de la copia solo con el mismo accountId; y la vista previa usa `skipHtml`, `urlTransform` con http, https y mailto, imágenes como texto y enlaces con `rel="noopener noreferrer"`. Las desviaciones declaradas son aceptables. Quedan tres Minor: una carrera en el cierre de sesión, un comentario obsoleto en el CI y la falta de prueba automática contra la biblioteca de acceso real.
