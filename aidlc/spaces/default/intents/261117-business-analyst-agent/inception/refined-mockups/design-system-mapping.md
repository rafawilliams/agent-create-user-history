# Design System Mapping — Business Analyst Agent

Documentos de entrada: `wireframes.md`, `user-flow.md`, `stories.md`, `requirements.md` y `team-practices.md`. Respuestas: `refined-mockups-questions.md` (RF Qn). Detalle de componentes: `interaction-spec.md`.

## Decisiones de sistema de diseño

| Tema | Decisión | Fuente |
|------|----------|--------|
| Guía de estilo | Material Design | `rough-mockups-questions.md` (Q6); RF Q1 |
| Librería | MUI (Material UI) para React | RF Q1 |
| Temas | Claro y oscuro, según la preferencia del sistema del usuario | RF Q2 |
| Paleta | La paleta por defecto de Material Design | RF Q3 |
| Idioma de la interfaz | Español, con identificadores del código en inglés | `requirements.md` (FR2.4); `team-practices.md` (Code Style) |

## Mapeo de componentes

| Componente de la interfaz | Componente MUI | Notas |
|---------------------------|----------------|-------|
| AppHeader | `AppBar` + `Toolbar` | Nombre del agente a la izquierda y "Cerrar sesion" a la derecha en escritorio |
| LogoutButton (móvil) | `IconButton` + `Menu` | Agrupa Cerrar sesion en un menú (decisión de diseño) |
| TitleField | `TextField` (variante outlined) con `helperText` y `inputProps.maxLength` | El contador N / 200 va en el texto de ayuda |
| ContextField | `TextField` multilínea | Aparece solo cuando el título es ambiguo |
| GenerateButton | `Button` (contained) | Desactivado mientras se genera |
| ResultTabs | `Tabs` + `Tab` + paneles | "Vista previa" y "Markdown" |
| Vista previa | contenido formateado en un `Paper` | El Gherkin va en un bloque de código |
| Markdown | texto en bloque de código dentro de un `Paper` | Texto seleccionable |
| CopyButton | `Button` (outlined) + `Snackbar` o texto de estado | Confirmación con icono y texto |
| StatusMessage (carga) | `CircularProgress` con texto | Región de estado |
| StatusMessage (error, aviso) | `Alert` (severidad error y warning) | Icono y texto |
| LoginButtons | `Button` (outlined) por proveedor | Texto "Continuar con Gmail" y "Continuar con Outlook" |

## Tokens de diseño

Se usan los valores por defecto del tema de MUI: tipografía Roboto, espaciado base de 8 px y esquinas redondeadas estándar (RF Q1, Q3). Los dos temas se definen con la paleta por defecto en versión clara y oscura (RF Q2, Q3). No se definen tokens propios en esta etapa.

| Token | Valor | Nota |
|-------|-------|------|
| Color primario | por defecto de MUI | Debe cumplir contraste 4.5:1 con el texto en ambos temas |
| Color de error | por defecto de MUI | Siempre acompañado de icono y texto |
| Espaciado | múltiplos de 8 px | Valor por defecto de MUI |
| Tamaño táctil mínimo | 44 por 44 px | Valor de referencia de la guía de accesibilidad WCAG 2.1 AA de esta etapa, no una respuesta confirmada; ver `accessibility-checklist.md` |

## Comportamiento responsive

| Ancho | Comportamiento | Fuente |
|-------|----------------|--------|
| Móvil | Una columna; botones a todo el ancho; Cerrar sesion en un menú | RF Q5; `mockups.md` |
| Escritorio | Contenido centrado con un ancho máximo legible; Cerrar sesion visible en el encabezado | RF Q4 |

Se usan los puntos de corte por defecto de MUI. El punto exacto en que pasa a una columna queda abierto (la propuesta previa de `wireframes.md` era menos de 768 px).

## Cumplimiento con el sistema de diseño

- El proyecto no tiene hoy ningún sistema de diseño ni librería de interfaz (`business-overview.md` describe un script de línea de comandos), por lo que no hay componentes previos que reutilizar.
- La interfaz usa solo componentes de MUI y no crea componentes visuales propios fuera de la composición de los anteriores.

## Assumptions & Open Questions

- Abierto: punto de corte a una columna y la agrupación de Cerrar sesion en un menú en móvil.
- Abierto: versión de MUI y de React a usar; se decide en la etapa de diseño técnico.
- Abierto: forma de confirmar el copiado (texto junto al botón o `Snackbar`).
