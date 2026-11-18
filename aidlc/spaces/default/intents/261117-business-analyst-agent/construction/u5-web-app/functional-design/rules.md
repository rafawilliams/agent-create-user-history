# Reglas de negocio — u5-web-app

## Sources

- [Q1] Token solo en memoria.
- [Q2] Vista previa con una biblioteca de Markdown que no interpreta HTML en bruto.
- [Q3] Conservar lo escrito si la sesión vence.
- [scope] `interaction-spec.md`, `design-system-mapping.md` y `accessibility-checklist.md` de Refined Mockups; contratos C1 y C2 de `contract-summary.md`.

## BR5.1 Validación del título

Se valida solo al pulsar "Generar historia"; el contador "N / 200" se actualiza al escribir. La pantalla recorta los espacios de los bordes y cuenta en puntos de código Unicode, igual que el servicio (no en unidades de UTF-16). Vacío o solo espacios: mensaje "Escribe un titulo para generar la historia." y el foco vuelve al campo (AC1.1.3). Más de 200: mensaje "El titulo no puede superar 200 caracteres." sin llamar al servicio (AC1.1.2); con exactamente 200 se envía.

## BR5.2 Un solo envío a la vez

Mientras el estado es generating, el botón y los campos quedan desactivados y se ve un indicador de carga con texto en una región de estado (AC5.1.1). Un segundo clic no envía nada. Si la página se recarga durante generating, se pierde lo escrito y se vuelve a S2 vacío (Q3 solo cubre el vencimiento de sesión).

## BR5.3 Contexto

Si el servicio responde NEEDS_CONTEXT, la pantalla muestra el mensaje bajo el título y el campo de contexto con el foco; no muestra ninguna historia (AC1.1.4). El contexto se recorta y se cuenta igual que el título, con máximo 500 ("El contexto no puede superar 500 caracteres."); vacío o solo espacios no se envía y se muestra "Agrega contexto para generar la historia.". Al volver a pulsar, se envía el título y el contexto.

## BR5.4 Fallos, mensajes y reintento

La pantalla muestra siempre un texto propio en español (nunca el texto del servicio ni nada del cuerpo de la respuesta) con `role="alert"`, icono y texto. Tabla de traducción:

| Origen | Estado | Mensaje | Acción ofrecida |
|---|---|---|---|
| 200 con cuerpo sin `markdown` de texto (AC5.1.3) | failed | "No se pudo generar la historia. Inténtalo de nuevo." | Reintentar |
| NEEDS_CONTEXT (422) | needsContext | Mensaje de BR5.3 | Completar contexto |
| CONTEXT_TOO_LONG (400) | needsContext | "El contexto no puede superar 500 caracteres." | Editar contexto |
| TITLE_EMPTY o TITLE_TOO_LONG (400) | idle | Mensaje de BR5.1 | Editar título |
| RATE_LIMITED (429) | failed | "Hay demasiadas solicitudes. Espera 30 segundos e inténtalo de nuevo." | "Reintentar" desactivado 30 segundos |
| SESSION_INVALID (401) | sessionExpired | Mensaje de BR5.6 | Iniciar sesión de nuevo |
| ACCOUNT_NOT_ALLOWED (403, en C1 o C2) | accessDenied | "Tu cuenta no tiene acceso a este agente." | Cerrar sesión |
| GENERATION_TIMEOUT, MODEL_FAILURE, INVALID_MODEL_RESPONSE, cuerpos 5xx y cualquier otro código | failed | "No se pudo generar la historia. Inténtalo de nuevo." | Reintentar |
| Cuerpo que no es JSON o sin `code` (502, 504 o 429 de la pasarela), o falla de red | failed | "No se pudo generar la historia. Inténtalo de nuevo." | Reintentar |
| Sin respuesta a los 60 segundos | failed | "La generación superó los 60 segundos. Inténtalo de nuevo." | Reintentar |

"Reintentar" genera de nuevo con el título (y el contexto) conservados (AC5.1.2). La respuesta que llegue después de abortar a los 60 s se descarta. Nunca se muestra texto parcial como resultado (AC5.1.3). Cuando el servicio marca un fallo como no reintentable, "Reintentar" no se ofrece: se ofrece la acción de la tabla si existe, o solo "Generar historia", que vuelve a estar disponible al editar un campo.

## BR5.5 Resultado

La historia aparece en las pestañas "Vista previa" y "Markdown" con el mismo contenido (AC4.1.1). La vista previa se construye con una biblioteca que no interpreta HTML en bruto (Q2). Solo se permiten enlaces `http`, `https` y `mailto`, que abren en otra pestaña con `rel="noopener noreferrer"`; las imágenes no se cargan (se muestran como texto). El Markdown se muestra como texto seleccionable. "Copiar Markdown" copia exactamente el Markdown recibido, sin transformarlo, y confirma con el texto "Markdown copiado" y un icono anunciado en una región de estado; si el navegador rechaza la copia se muestra el aviso "No se pudo copiar. Selecciona el texto y cópialo a mano." (AC4.1.2). Que lo pegado en Jira conserve títulos, lista y Gherkin depende del Markdown que construye el servicio y de este copiado exacto (AC4.1.3); que un título con caracteres especiales no altere el formato depende del escape del servicio (AC4.1.4).

## BR5.6 Sesión vencida

El vencimiento se comprueba al pulsar "Generar historia" (con el `exp` del token) y cuando una llamada responde SESSION_INVALID. Si ocurre, el estado pasa a sessionExpired: mensaje "Tu sesión terminó. Inicia sesión de nuevo para continuar.", botón "Iniciar sesión de nuevo" y copia temporal de título y contexto (ENT-003). Una generación en curso no se cancela, pero si su resultado llega con la sesión ya vencida se descarta. Al volver del inicio de sesión se llama a GET /v1/session; si responde 200 y su `accountId` coincide con el guardado en la copia (ENT-003), la pantalla pasa a idle con el título y el contexto restaurados (o a needsContext si había contexto) y la copia se borra.

## BR5.7 Inicio de sesión

Sin token, la pantalla muestra solo S1 con "Continuar con Gmail" y "Continuar con Outlook"; no redirige sola, por lo que no puede haber un bucle de redirecciones. Un visitante sin token que abre la pantalla, o que llega a S2 sin token (por ejemplo tras un token vencido), es llevado a S1 antes de poder generar (AC6.1.2). Al pulsar un botón se inicia el flujo de código con PKCE de Cognito (BR5.10). Mientras vuelve la respuesta se ve "Iniciando sesión" (estado signingIn). Si el proveedor falla o la persona cancela, se borra la copia temporal si existe y S1 muestra "No se pudo iniciar sesión. Inténtalo de nuevo." con `role="alert"` y los dos botones siguen disponibles (AC6.1.3). Con ACCOUNT_NOT_ALLOWED se aplica la fila de BR5.4.

## BR5.8 Cierre de sesión

"Cerrar sesion" en el encabezado (en móvil, dentro de un menú) llama a DELETE /v1/session, borra el token y toda copia temporal de memoria y de sessionStorage y redirige al cierre de sesión de Cognito, que cierra su sesión y regresa a S1 por una dirección de retorno registrada. Así, el siguiente "Continuar con Gmail" ya no entra solo por la sesión de Cognito (la sesión de Google o de Microsoft en el navegador sigue siendo de ellos y puede aprobar el acceso sin pedir credenciales). Si DELETE falla se continúa igualmente: el servicio no guarda estado y no invalida el token (riesgo aceptado en u4), por lo que el cierre efectivo es el de Cognito.

## BR5.9 Accesibilidad e idioma

Todo el texto visible está en español, con identificadores en inglés. Los temas claro y oscuro siguen la preferencia del sistema; los errores siempre llevan icono y texto; el tamaño táctil mínimo es de 44 por 44 píxeles; el orden de foco y los roles están en `accessibility-checklist.md`.

## BR5.10 Flujo PKCE

- Al pulsar un botón la pantalla genera un `code_verifier` y un `state` aleatorios y guarda solo esos dos valores, junto con la copia temporal de BR5.6 si existe, en sessionStorage durante la redirección: es la única excepción a Q1 y nunca incluye el token.
- Al volver, la pantalla exige que `state` coincida con el guardado; si no coincide o falta, se trata como fallo de inicio (BR5.7). Luego intercambia el `code` por tokens y borra de inmediato el `code_verifier`, el `state` y los parámetros `code` y `state` de la dirección de la página (con `history.replaceState`).
- El token enviado en `Authorization: Bearer` es el token de identidad (C3 exige `token_use` igual a `id`). Se mantiene solo en memoria (Q1) y su `exp` es la fecha de vencimiento de BR5.6.
- La dirección de retorno es un valor exacto, la raíz del sitio, y la de cierre de sesión es la misma; u6-infrastructure las registra en el cliente de Cognito y define el dominio del grupo.
- El cliente de Cognito es público (sin secreto). El access token y el refresh token quedan solo en el objeto de usuario en memoria de la biblioteca: no se usan, no se envían a ninguna parte y no hay renovación; solo se usa el token de identidad y, al vencer, se vuelve a iniciar sesión.
- Al recargar la página sin token se muestra S1; no se intenta un inicio silencioso (pulsar un botón no pide credenciales si la sesión de Cognito sigue activa).

## Assumptions & Open Questions

None.
