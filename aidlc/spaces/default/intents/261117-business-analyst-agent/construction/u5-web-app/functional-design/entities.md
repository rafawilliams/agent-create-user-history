# Entidades — u5-web-app

Solo viven en la memoria de la página; la interfaz no guarda nada en el servidor (decisión de Q1: el token solo en memoria; decisión de Q3: copia temporal de los campos). Cuando se dice "la pantalla" se habla de la aplicación React con MUI de `web/`.

## Sources

- [Q1] Token de sesión solo en memoria de la página.
- [Q3] Título y contexto se conservan durante la redirección de un inicio de sesión nuevo.
- [scope] `requirements.md` (FR1 a FR6) y `components.md` (la pantalla y el cliente del servicio); contratos C1 y C2 de `contract-summary.md`; criterios AC1.1.1 a AC6.1.3.

## ENT-001 AccessToken

| Campo | Tipo | Regla |
|---|---|---|
| value | texto | Token de identidad (`token_use` id) emitido por Cognito; nunca se escribe en el almacenamiento del navegador, en la dirección de la página ni en los registros de la consola; durante la redirección PKCE solo se guardan el verificador y el estado (BR5.10) |
| expiresAt | fecha | Se lee del `exp` del token y se comprueba al pulsar "Generar historia" (BR5.6) |

## ENT-002 ScreenState

Estado único de la pantalla principal (S2). Un solo valor a la vez.

| Estado | Significado |
|---|---|
| signedOut | Sin token: se muestra S1 |
| signingIn | Esperando la respuesta del proveedor: se muestra "Iniciando sesión" |
| idle | S2 vacío o con el título escrito |
| needsContext | El servicio pidió contexto (NEEDS_CONTEXT) |
| generating | Generación en curso, controles bloqueados |
| result | Hay una historia que mostrar |
| failed | Fallo del servicio, de la red o de los 60 s, con "Reintentar" |
| sessionExpired | El servicio respondió SESSION_INVALID o el token venció |
| accessDenied | El servicio respondió ACCOUNT_NOT_ALLOWED |

## ENT-003 Draft

| Campo | Tipo | Regla |
|---|---|---|
| title | texto | Hasta 200 caracteres; no vacío ni solo espacios al enviar |
| context | texto | Hasta 500 caracteres; solo visible en needsContext |
| accountId | texto | El `accountId` de GET /v1/session al guardar la copia; al restaurar debe coincidir con el de la sesión nueva |

Se copia al almacenamiento de sesión de la pestaña únicamente al pasar a sessionExpired (BR5.6). Se borra al restaurarlo con la misma cuenta, al fallar o cancelarse el inicio de sesión, con ACCOUNT_NOT_ALLOWED y al cerrar la sesión. No contiene el token.

## ENT-004 StoryResult

| Campo | Tipo | Regla |
|---|---|---|
| markdown | texto | El Markdown completo que devuelve C1; es la única fuente de las dos pestañas |
| requestId | texto | Solo para mostrar en el mensaje de soporte si falla algo |

## Assumptions & Open Questions

None.
