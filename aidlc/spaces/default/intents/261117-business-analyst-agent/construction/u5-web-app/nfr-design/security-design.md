# Security Design — u5-web-app

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: Q1 (biblioteca de inicio de sesión) y el diseño funcional ya fijaron las decisiones.

## Sources

- [Q1] `oidc-client-ts` para el inicio de sesión.
- [scope] `security-requirements.md` NFR4.1 a NFR4.4 y NFR5.1 a NFR5.5; `rules.md` BR5.5, BR5.6, BR5.8 y BR5.10.

## Configuración de la biblioteca de inicio de sesión

| Ajuste | Valor | Requisito |
|--------|-------|-----------|
| Flujo | Código con PKCE (S256), `response_type` igual a `code`, alcance `openid email`, sin secreto de cliente | NFR5.1, NFR5.2 |
| `userStore` | `WebStorageStateStore` sobre `InMemoryWebStorage` | NFR4.1 |
| `stateStore` | `WebStorageStateStore` sobre sessionStorage (verificador y estado solo durante la redirección) | NFR4.1, NFR5.2 |
| Renovación | `automaticSilentRenew` desactivado, sin iframe de renovación; `loadUserInfo` desactivado | NFR4.1 |
| Metadatos | Explícitos y derivados solo de la configuración pública: emisor `https://cognito-idp.<región>.amazonaws.com/<grupo>`, autorización y token en el dominio del grupo, cierre en `https://<dominio>/logout` | NFR5.5 |
| Direcciones | Retorno y cierre de sesión: la raíz del sitio, valor exacto de configuración | NFR5.2, NFR5.5 |
| Configuración pública | Solo variables `VITE_` (región, grupo, dominio, cliente, origen del servicio), nunca secretos | NFR5.1 |

## Flujos

1. **Inicio:** el botón del proveedor llama a `signinRedirect` con `extraQueryParams: { identity_provider: <nombre> }`, donde el nombre es exactamente `Google` o `Microsoft`, los nombres de los proveedores que u6-infrastructure define en el grupo de Cognito (se registran en la sección de requisitos de alojamiento de `contract-summary.md` y u4 los reconoce como `google` y `microsoft` sin distinguir mayúsculas); la biblioteca guarda verificador y estado en sessionStorage junto con la copia temporal de BR5.6 si existe.
2. **Regreso:** al arrancar, `config` y `authClient` miran la dirección. Si trae `code` y `state`, o `error` (con o sin `state`), se procesa el retorno exactamente una vez: una variable de módulo (no un efecto de React) guarda la promesa del callback, de modo que el doble efecto de `StrictMode` (que `web/src/main.tsx` ya usa) reutiliza la misma promesa y no consume el `code` dos veces. La dirección completa se captura primero y se entrega al callback; justo después se llama a `history.replaceState` para borrar `code`, `error`, `error_description` y `state`, tenga éxito o falle el retorno. La promesa a nivel de módulo se reinicia con la recarga en caliente de Vite (solo en desarrollo), y la prueba de este flujo se ejecuta con `StrictMode` activo. Con éxito, la pantalla llama a GET /v1/session; si esa llamada falla (red, 5xx) se muestra la fila de fallo de BR5.4 con el botón para reintentar la comprobación y el token sigue en memoria; con ACCOUNT_NOT_ALLOWED pasa a accessDenied. Con un error (estado distinto, cancelación con `error` o proveedor caído) se muestra el mensaje de BR5.7 y se borra la copia temporal.
3. **Uso:** el dueño del token es `auth/sessionHolder`, que lo obtiene del `User` de la biblioteca una sola vez al volver del acceso y no guarda otra copia persistente; antes de cada generación comprueba `exp` (BR5.6) y lo añade como `Authorization: Bearer`. El `userStore` en memoria de la biblioteca existe solo por su propia mecánica y `removeUser()` lo vacía al cerrar la sesión.
4. **Cierre:** en este orden: DELETE /v1/session (un fallo no detiene el cierre), `removeUser()`, borrado de la copia temporal y navegación (`window.location.assign`) a `https://<dominio>/logout?client_id=<cliente>&logout_uri=<retorno codificado>`, armada por `authClient` porque Cognito no publica `end_session_endpoint` (NFR5.5).

## Protecciones

| Amenaza | Diseño | Requisito |
|---------|--------|-----------|
| Token en almacenamiento | El único almacén de usuario es en memoria; una prueba revisa localStorage y sessionStorage tras el inicio y el cierre | NFR4.1, NFR5.5 |
| Fuga por la consola | La aplicación no llama a `console.*` con datos; los errores del cliente de C1 se traducen a un código y un mensaje propio sin el cuerpo de la respuesta | NFR4.2 |
| XSS por el texto del modelo | La vista previa usa `react-markdown` con `skipHtml`, sin plugin de HTML en bruto; `urlTransform` devuelve una cadena vacía para todo esquema que no sea `http`, `https` o `mailto`; `components.img` se sustituye por un elemento de texto con el texto alternativo (nunca un `img`) y `components.a` produce un enlace con `target="_blank"` y `rel="noopener noreferrer"` (sin `href` si el esquema no se permite). El Markdown se muestra además como texto en un bloque | NFR4.3 |
| Copia temporal | Clave única en sessionStorage con título, contexto y `accountId`; se borra en cada salida de NFR4.4 (incluida la de un `accountId` distinto, caso en que la pantalla pasa a idle con campos vacíos y un aviso de que se descartó lo guardado) y nunca incluye el token | NFR4.4 |
| Cabeceras y política de contenido | La cabecera exacta de NFR5.4 la sirve u6; u5 no usa scripts en línea ni `eval` y una prueba inspecciona `dist/index.html` y falla ante cualquier `<script>` sin `src`; los recursos pequeños que Vite inserta como `data:` están permitidos para fuentes e imágenes | NFR5.4 |
| Secretos en el paquete | Búsqueda de patrones de claves de AWS y de secretos en `dist/` y revisión de que la configuración solo toma variables públicas | NFR5.1 |
| Dependencias | `npm ci` desde el archivo de bloqueo, versión exacta de `oidc-client-ts` y `react-markdown`, y `npm audit --omit=dev --audit-level=high` bloqueante | NFR5.3 |

## Assumptions & Open Questions

- Supuesto: la biblioteca conserva el access token y el refresh token solo dentro del objeto de usuario en memoria; no se usan ni se envían.
- Abierto: el servidor de contenido y la política exacta los entrega u6-infrastructure (NFR5.4); aquí solo se prueban las propiedades del paquete.
