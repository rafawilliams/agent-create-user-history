# Logical Components — u5-web-app

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`.

## Sources

- [scope] `functional-spec.md` (módulos por responsabilidad), `frontend-components.md` del diseño funcional y las decisiones de `performance-design.md` y `security-design.md`.

## Inventario de módulos de la pantalla (`web/src/`)

| Módulo | Responsabilidad | Reglas y requisitos |
|--------|-----------------|---------------------|
| `config` | Lee las variables públicas `VITE_` y las valida al arrancar; sin ellas la pantalla muestra un error de configuración y no inicia sesión | NFR5.1 |
| `auth/authClient` | Envuelve `oidc-client-ts`: inicio con el proveedor, callback, limpieza de la dirección, cierre con `logout_uri` | BR5.7, BR5.8, BR5.10; NFR5.2, NFR5.5 |
| `auth/sessionHolder` | Dueño del token de identidad y su `exp` solo en memoria (lo toma del usuario de la biblioteca al volver del acceso); entrega el token si no ha vencido | BR5.6; NFR4.1 |
| `api/client` | C1 (generar) y C2 (comprobar y cerrar sesión) con temporizador de 60 s, un solo envío y traducción de errores a la tabla de BR5.4 | BR5.2, BR5.4; NFR1.1, NFR3.1 |
| `state/screenState` | Un solo estado de pantalla (ENT-002) y sus transiciones, incluido accessDenied y sessionExpired | BR5.2 a BR5.7 |
| `draft/draftStore` | Copia temporal de título, contexto y `accountId` en sessionStorage, con su ciclo de vida de borrado | BR5.6; NFR4.4 |
| `components/*` | LoginButtons, AppHeader y LogoutButton, TitleField, ContextField, GenerateButton, StatusMessage y su composición en S1 y S2 | `frontend-components.md` |
| `components/ResultView` | ResultTabs, vista de Markdown como texto y CopyButton; contiene `MarkdownPreview` (carga diferida) detrás de una barrera de errores | BR5.5; NFR1.3 |
| `components/MarkdownPreview` (carga diferida) | Vista previa con `react-markdown`, `skipHtml`, `urlTransform`, `components.a` y `components.img` | BR5.5; NFR1.3, NFR4.3 |
| `theme` | Tema de MUI claro y oscuro por preferencia del sistema, con `minHeight` y `minWidth` de 44 px | BR5.9; NFR7.1 |
| `scripts/check-bundle` | Medición del presupuesto de 400 KB y de la carga diferida | NFR1.3 |

## Dominios de falla

| Dominio | Qué falla | Efecto sobre la persona | Contención |
|---------|-----------|-------------------------|------------|
| Inicio de sesión (Cognito) | Proveedor, red o estado no válido | S1 con mensaje y botones disponibles | La copia temporal se borra; ninguna llamada al servicio |
| Servicio de historias (C1, C2) | Error, 429, 5xx, 60 s o cuerpo inesperado | Mensaje propio y la acción de la tabla de BR5.4 | Título y contexto conservados; respuesta tardía descartada |
| Vista previa (carga diferida) | No se descarga el paquete de la vista previa | Aviso con botón para reintentar la carga; la pestaña Markdown y el botón de copiar siguen funcionando | Solo `MarkdownPreview` es diferido y está detrás de una barrera de errores |
| Portapapeles del navegador | Rechaza la copia | Aviso para copiar a mano | Markdown seleccionable |

## Recursos compartidos

- Configuración pública (`config`), usada por `auth` y `api`.
- sessionStorage de la pestaña: solo verificador, estado y copia temporal (NFR4.1, NFR4.4).
- El token en memoria (`auth/sessionHolder`) es lo único con acceso al token; ningún otro módulo lo guarda.

## Assumptions & Open Questions

- Supuesto: la estructura de archivos concreta se decide en Code Generation; este inventario fija responsabilidades y límites.
- Abierto: la entrega de la cabecera de política de contenido y del alojamiento estático es de u6-infrastructure.
