# Interaction Spec — Business Analyst Agent

Documentos de entrada: `wireframes.md`, `user-flow.md`, `stories.md`, `requirements.md` y `team-practices.md`. Mockups: `mockups.md`. Respuestas: `refined-mockups-questions.md` (RF Qn). Formato de componentes: `component-spec-template.md`.

## Flujo de interacción principal

1. S1: la persona elige Gmail u Outlook (US6.1). Con éxito pasa a S2; si falla, S1 muestra un mensaje y los botones siguen disponibles (RF Q7).
2. S2 vacío: escribe el título; el contador se actualiza al escribir (RF Q6).
3. Pulsa "Generar historia": se valida el título; si es válido pasa a cargando (US1.1, US5.1).
4. Si el título es ambiguo, aparece el mensaje y el campo de contexto; completa el contexto y vuelve a pulsar (US1.1).
5. Con resultado: cambia entre "Vista previa" y "Markdown" y pulsa "Copiar Markdown" (US4.1).
6. Si falla: mensaje y "Reintentar" con el título conservado (US5.1).
7. Cierra sesión desde el encabezado (RF Q4).

## Reglas de validación

| Campo | Regla | Mensaje | Fuente |
|-------|-------|---------|--------|
| Título | Obligatorio (no vacío ni solo espacios) | "Escribe un titulo para generar la historia." (borrador) | AC1.1.3 |
| Título | Máximo 200 caracteres; el contador muestra N / 200 | "El titulo no puede superar 200 caracteres." (borrador) | AC1.1.2, RF Q6 |
| Título | Muy corto o ambiguo: se pide contexto | "El titulo es muy corto. Agrega contexto." (borrador) | AC1.1.4 |

Se valida al pulsar "Generar historia"; el contador se actualiza mientras se escribe. El mensaje de error aparece debajo del campo, con icono y texto (no solo color).

## Componentes

### TitleField

| Campo | Valor |
|---|---|
| Componente | TitleField |
| Descripción | Campo de texto para el título de la funcionalidad, con contador |
| Categoría | input |

| Estado | Descripción | Disparador |
|---|---|---|
| default | Vacío, con texto de ejemplo | carga de la pantalla |
| focus | Foco del teclado | Tab o clic |
| error | Mensaje debajo del campo | validación fallida al enviar |
| disabled | Solo lectura mientras se genera | generación en curso |

| Prop | Tipo | Obligatorio | Valor por defecto | Descripción |
|---|---|---|---|---|
| value | string | sí | vacío | Texto del título |
| maxLength | number | sí | 200 | Límite de caracteres (FR1.2) |
| errorText | string | no | — | Mensaje de error visible |

| Requisito de accesibilidad | Implementación |
|---|---|
| Rol | campo de texto nativo con etiqueta visible "Titulo de la funcionalidad" |
| Teclado | Tab para enfocar; Enter envía |
| Error | mensaje asociado con `aria-describedby`; icono y texto |
| Contador | anunciado como texto, no solo visual |

Responsive: a todo el ancho en móvil y en escritorio.

### ContextField

| Campo | Valor |
|---|---|
| Componente | ContextField |
| Descripción | Campo adicional que aparece cuando el título es ambiguo |
| Categoría | input |

Estados: oculto por defecto; visible tras la petición de contexto, con el foco al aparecer. Accesibilidad: etiqueta visible "Contexto"; el mensaje de petición se asocia con `aria-describedby`; el foco pasa al campo cuando aparece. El límite de longitud y la validación de vacío siguen abiertos (`requirements.md`).

### GenerateButton

| Campo | Valor |
|---|---|
| Componente | GenerateButton |
| Descripción | Botón principal que inicia la generación |
| Categoría | input |

Estados: default; focus; disabled mientras se genera (evita envíos dobles, FR5.1). Accesibilidad: botón nativo; Enter o Espacio lo activan; tamaño táctil de al menos 44 por 44 píxeles; a todo el ancho en móvil (RF Q5).

### ResultTabs

| Campo | Valor |
|---|---|
| Componente | ResultTabs |
| Descripción | Pestañas "Vista previa" y "Markdown" con el mismo contenido |
| Categoría | navigation |

Estados: pestaña activa; pestaña inactiva; focus. Accesibilidad: rol `tablist` con pestañas `tab` y paneles `tabpanel`; flechas izquierda y derecha cambian de pestaña; Tab entra al panel; se anuncia la pestaña activa.

### CopyButton

| Campo | Valor |
|---|---|
| Componente | CopyButton |
| Descripción | Copia el Markdown al portapapeles y confirma |
| Categoría | input / feedback |

Estados: default; focus; copiado (mensaje "Markdown copiado" con icono). Accesibilidad: botón nativo; la confirmación se anuncia con una región de estado (`aria-live="polite"`), no solo por color. A todo el ancho en móvil (RF Q5).

### StatusMessage

| Campo | Valor |
|---|---|
| Componente | StatusMessage |
| Descripción | Mensajes de carga, error, aviso y confirmación |
| Categoría | feedback |

| Variante | Rol / anuncio | Icono |
|---|---|---|
| cargando | región de estado `aria-live="polite"` | indicador de carga |
| error del servicio | `role="alert"` y el foco pasa a "Reintentar" | (x) |
| aviso (contexto) | texto asociado al campo | (!) |
| confirmación (copiado) | `aria-live="polite"` | (ok) |

### LoginButtons

| Campo | Valor |
|---|---|
| Componente | LoginButtons |
| Descripción | Botones "Continuar con Gmail" y "Continuar con Outlook" |
| Categoría | input |

Estados: default; focus; error de acceso (mensaje arriba, botones disponibles, RF Q7). Accesibilidad: botones nativos con texto visible; el mensaje de fallo usa `role="alert"`.

### AppHeader y LogoutButton

Encabezado con el nombre del agente y, en S2, el botón "Cerrar sesion" (RF Q4). En móvil, el botón pasa a un menú del encabezado (decisión de diseño, ver `mockups.md`). Accesibilidad: regiones `header` y `main`; el botón es nativo.

## Estados por pantalla

| Pantalla | Vacío | Cargando | Éxito | Error | Parcial / borde |
|----------|-------|----------|-------|-------|-----------------|
| S1 | estado inicial | (sin definir en esta etapa) | pasa a S2 | mensaje de acceso | — |
| S2 | sí | sí | sí | sí (servicio y validación) | título ambiguo; título de 200 caracteres; título vacío |

## Assumptions & Open Questions

- Abierto: estado "iniciando sesión" de S1 (qué se ve mientras el proveedor responde).
- Abierto: duración del mensaje "Markdown copiado" y comportamiento si la copia al portapapeles es rechazada por el navegador.
- Abierto: límite y validación del campo de contexto.
- Abierto: qué pasa con el contenido escrito si la sesión expira a mitad de una generación.
